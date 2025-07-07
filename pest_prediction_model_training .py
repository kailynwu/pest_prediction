import pandas as pd
import os
import joblib  # 新增：导入joblib用于模型保存
from sklearn.preprocessing import MultiLabelBinarizer
from xgboost import XGBClassifier
from sklearn.metrics import classification_report

# 1. 数据加载与预处理（保持不变）
df = pd.read_csv("data/orchard_pest_disease_dataset.csv")
df['日期'] = pd.to_datetime(df['日期'])
df = df.sort_values('日期')

mlb = MultiLabelBinarizer()
pest_labels = df['病虫害'].apply(lambda x: x.split(', ') if x != '无' else [])
binary_labels = mlb.fit_transform(pest_labels)
label_df = pd.DataFrame(binary_labels, columns=mlb.classes_)

features = df[['温度 (°C)', '湿度 (%)', '降雨量 (mm)']]
labels = label_df


# 2. 构造时序特征（保持不变）
def create_window_features(features, window=15):
    window_features = features.rolling(window=window, min_periods=window).mean().dropna()
    aligned_labels = labels.iloc[window - 1:]
    return window_features, aligned_labels


window_features, aligned_labels = create_window_features(features)

# 3. 模型训练与保存（关键修改部分）
X = window_features[['温度 (°C)', '湿度 (%)', '降雨量 (mm)']]
y = aligned_labels

split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

os.makedirs("models", exist_ok=True)

# 整合多标签模型和二值化器
model_dict = {
    "mlb": mlb,  # 保存标签二值化器，预测时需要用
    "models": {}  # 存储各病虫害对应的分类器
}

# 训练每个病虫害的分类器并存储
for label in y_train.columns:
    clf = XGBClassifier(objective='binary:logistic', n_estimators=100)
    clf.fit(X_train, y_train[label])
    model_dict["models"][label] = clf  # 存入模型字典

    # 评估（保持原有逻辑）
    y_pred = clf.predict(X_test)
    print(f"\n标签 {label} 评估结果：")
    print(classification_report(y_test[label], y_pred, zero_division=0))

# 保存整合后的模型文件（替换原JSON保存方式）
joblib.dump(model_dict, "models/trained_model.joblib")
print("\n已保存整合模型到：models/trained_model.joblib")