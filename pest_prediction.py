import mysql.connector
from mysql.connector import Error
import getpass
import joblib
import json
import os
from datetime import datetime, timedelta

def get_db_credentials():
    """获取数据库连接信息（优先从本地配置读取，否则用户输入）"""
    config_path = "config/db_config.json"

    # 检查是否存在已保存的配置
    if os.path.exists(config_path):
        use_saved = input("\n检测到已保存的数据库配置，是否使用？(Y/n): ").strip().lower()
        if use_saved in ("", "y"):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    print("✅ 已加载本地数据库配置")
                    return saved_config
            except Exception as e:
                print(f"⚠️ 配置文件读取失败: {str(e)}，请重新输入")

    # 用户输入新配置
    print("\n=== 请输入数据库连接信息 ===")
    host = input("数据库主机地址（如localhost）: ").strip()
    port = input("数据库端口（默认3306）: ").strip() or "3306"
    user = input("数据库用户名: ").strip()
    password = getpass.getpass("数据库密码: ")

    # 询问是否保存配置
    save_config = input("\n是否保存当前配置到本地？(Y/n): ").strip().lower()
    if save_config in ("", "y"):
        os.makedirs("config", exist_ok=True)  # 创建config目录（如果不存在）
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": None
            }, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到: {config_path}")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": None
    }

def test_db_connection(credentials):
    """测试数据库连接并返回连接对象"""
    try:
        conn = mysql.connector.connect(**credentials)
        if conn.is_connected():
            print("✅ 数据库连接测试成功！")
            return conn
    except Error as e:
        print(f"❌ 连接失败: {str(e)}")
    return None

def get_databases(conn):
    """获取当前用户有权限访问的所有数据库"""
    with conn.cursor() as cursor:
        cursor.execute("SHOW DATABASES")
        return [db[0] for db in cursor.fetchall()]

def select_database(databases):
    """引导用户选择目标数据库"""
    print("\n=== 请选择目标数据库 ===")
    for idx, db in enumerate(databases, 1):
        print(f"{idx}. {db}")
    while True:
        try:
            choice = int(input("请输入数据库序号: ")) - 1
            if 0 <= choice < len(databases):
                return databases[choice]
            print("请输入有效序号（如1、2...）")
        except ValueError:
            print("请输入数字序号")

def get_table_columns(conn, db_name, table_name):
    """获取指定表的所有列名"""
    with conn.cursor() as cursor:
        conn.database = db_name  # 切换到目标数据库
        cursor.execute(f"DESCRIBE `{table_name}`")  # 反引号处理特殊表名
        return [col[0] for col in cursor.fetchall()]

def main():
    # 步骤1：获取并验证数据库连接（修改后逻辑）
    credentials = get_db_credentials()  # 改为调用支持配置读取的新函数
    conn = test_db_connection(credentials)
    if not conn:
        print("连接失败，程序终止")
        return

    try:
        # 步骤2：选择目标数据库和表
        databases = get_databases(conn)
        target_db = select_database(databases)

        # 获取数据库中的表
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW TABLES IN `{target_db}`")
            tables = [t[0] for t in cursor.fetchall()]

        print("\n=== 请选择数据所在表 ===")
        for idx, table in enumerate(tables, 1):
            print(f"{idx}. {table}")
        target_table = tables[int(input("请输入表序号: ")) - 1]

        # 步骤3：列映射配置
        columns = get_table_columns(conn, target_db, target_table)
        print(f"\n表 `{target_db}`.`{target_table}` 的列: {columns}")

        column_map = {}
        for field in ["日期", "温度", "湿度", "降雨"]:
            while True:
                col = input(f"请输入{field}对应的列名: ").strip()
                if col in columns:
                    column_map[field] = col
                    break
                print(f"列名不存在，请从 {columns} 中选择")

        # 步骤4：加载模型（假设模型文件为trained_model.joblib）
        try:
            model_dict = joblib.load("models/trained_model.joblib")  # 重命名为model_dict更清晰
            mlb = model_dict["mlb"]  # 提取标签二值化器
            pest_models = model_dict["models"]  # 提取各病虫害分类器字典
            print("✅ 模型加载成功")
        except FileNotFoundError:
            print("❌ 未找到模型文件trained_model.joblib")
            return

        # 步骤5：读取未来15天数据（示例：假设日期列是DATE类型）
        start_date = datetime.strptime(
            input("\n请输入预测起始日期（格式YYYY-MM-DD）: "),
            "%Y-%m-%d"
        )
        end_date = start_date + timedelta(days=15)

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(f"""
                SELECT {column_map['日期']} AS date,
                       {column_map['温度']} AS temp,
                       {column_map['湿度']} AS humidity,
                       {column_map['降雨']} AS rainfall
                FROM `{target_db}`.`{target_table}`
                WHERE {column_map['日期']} BETWEEN %s AND %s
            """, (start_date.date(), end_date.date()))
            raw_data = cursor.fetchall()

        if not raw_data:
            print("❌ 未找到未来15天的有效数据")
            return

        # 步骤6：模型预测（调整为多标签预测逻辑）
        features = [[d['temp'], d['humidity'], d['rainfall']] for d in raw_data]
        all_pest_probabilities = []  # 存储每个样本的所有病虫害概率

        # 遍历每个样本特征
        for sample in features:
            sample_probs = {}
            # 遍历每个病虫害对应的分类器
            for pest_type, clf in pest_models.items():
                # 二分类器输出正类概率（索引1）
                prob = clf.predict_proba([sample])[0][1]
                sample_probs[pest_type] = prob
            all_pest_probabilities.append(sample_probs)

        # 步骤7：保存预测结果到数据库（关键修改：添加float类型转换）
        with conn.cursor() as cursor:
            # 创建结果表（如果不存在）
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{target_db}`.pest_prediction_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    predict_date DATE COMMENT '预测日期',
                    pest_type VARCHAR(50) COMMENT '病虫害类型',
                    probability FLOAT COMMENT '发病概率',
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 插入预测结果（修改此处）
            for i, data in enumerate(raw_data):
                sample_probs = all_pest_probabilities[i]
                pest_type = max(sample_probs, key=lambda k: sample_probs[k])
                prob = sample_probs[pest_type]
                # 将numpy.float32转换为Python原生float类型
                prob = float(round(prob, 4))  # 关键修改点

                cursor.execute(f"""
                    INSERT INTO `{target_db}`.pest_prediction_results 
                    (predict_date, pest_type, probability)
                    VALUES (%s, %s, %s)
                """, (data['date'], pest_type, prob))

            conn.commit()
            print(f"✅ 已保存{len(raw_data)}条预测结果到`{target_db}`.pest_prediction_results")

    except Exception as e:
        print(f"❌ 程序执行出错: {str(e)}")
    finally:
        if conn.is_connected():
            conn.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    main()
