# 果园病虫害预测模型
## 项目概述
该项目是一个基于气象数据预测果园未来病虫害发生概率的工具。该系统通过连接数据库获取历史气象数据，使用训练好的机器学习模型预测未来 15 天内可能发生的病虫害类型及其概率，并将结果保存回数据库，帮助果园管理者提前做好病虫害防治准备。
## 项目结构
```plaintext
果园病虫害预测模型/
├── .idea/                  # IDE配置文件
├── config/                 # 数据库配置文件
│   └── db_config.json
├── models/                 # 训练好的模型文件
│   ├── 红蜘蛛_model.json
│   ├── 二斑叶螨_model.json
│   ├── 苹果金纹细蛾_model.json
│   └── trained_model.joblib
├── data/                   # 数据集文件
│   └── orchard_pest_disease_dataset.csv
├── pest_prediction.py      # 病虫害预测脚本
├── pest_prediction_model_training.py  # 模型训练脚本
└── README.md               # 项目说明文档
```
## 环境依赖
Python 3.x
mysql-connector-python：用于连接和操作 MySQL 数据库
joblib：用于模型的保存和加载
pandas：用于数据处理和分析
scikit-learn：用于数据预处理和模型评估
xgboost：用于构建和训练预测模型

### 你可以使用以下命令安装所需的依赖：
```plaintext
pip install mysql-connector-python joblib pandas scikit-learn xgboost
```
## 数据库配置
在 config/db_config.json 文件中配置数据库连接信息，示例如下：
```plaintext
{
    "host": "localhost",
    "port": "3306",
    "user": "root",
    "password": " ",
    "database": null
}
```
运行 pest_prediction.py 脚本时，程序会优先尝试加载该配置文件，也支持用户手动输入配置信息并保存。
## 模型训练
运行 pest_prediction_model_training.py 脚本进行模型训练：
```plaintext
python pest_prediction_model_training.py
```
脚本会执行以下步骤：

数据加载与预处理：从 data/orchard_pest_disease_dataset.csv 文件中加载数据，对日期进行格式化处理，并对病虫害标签进行二值化处理。
构造时序特征：使用滑动窗口方法构造时序特征，以捕捉气象数据的时间序列信息。
模型训练与保存：使用 XGBoost 为每个病虫害类型训练一个二分类器，并将所有模型和标签二值化器保存到 models/trained_model.joblib 文件中。
模型评估：打印每个病虫害类型的分类报告，评估模型性能。
## 病虫害预测
运行 pest_prediction.py 脚本进行病虫害预测：
```plaintext
python pest_prediction.py
```

脚本会执行以下步骤：
获取并验证数据库连接：优先从 config/db_config.json 文件中加载数据库配置信息，若文件不存在或加载失败，提示用户手动输入。测试数据库连接，若连接失败，程序终止。
选择目标数据库和表：列出当前用户有权限访问的所有数据库，让用户选择目标数据库。然后列出目标数据库中的所有表，让用户选择数据所在的表。
列映射配置：获取所选表的所有列名，提示用户输入日期、温度、湿度和降雨对应的列名，确保数据读取正确。
加载模型：尝试从 models/trained_model.joblib 文件中加载训练好的模型和标签二值化器，若文件不存在，程序终止。
读取未来 15 天数据：提示用户输入预测起始日期，从数据库中读取未来 15 天的气象数据。若未找到有效数据，程序终止。
模型预测：对读取的气象数据进行特征提取，使用加载的模型预测每个样本的所有病虫害发生概率。
保存预测结果到数据库：在目标数据库中创建 pest_prediction_results 表（如果不存在），将预测结果插入该表，包括预测日期、病虫害类型和发病概率。
## 注意事项
请确保 data/orchard_pest_disease_dataset.csv 文件存在，且包含所需的字段（日期、温度、湿度、降雨量、病虫害等）。
在运行预测脚本前，请确保 models/trained_model.joblib 文件存在，否则会提示未找到模型文件。
数据库中需要有相应的权限来创建表和插入数据。
## 贡献
如果你想为这个项目做出贡献，请提交 Pull Request 或创建 Issue。
## 许可证
本项目采用 `BSD - 2 - Clause` 许可证。以下是许可证的详细内容：

```plaintext
BSD 2-Clause License

Copyright (c) 2025, kailynwu
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```