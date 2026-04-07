import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report

import joblib
df = pd.read_csv('Mediapipe_ML_V6.csv')
X = df.iloc[:, :-1] 
y = df.iloc[:, -1]

le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=40)

# 2. XGBoost 모델 생성 및 학습
# n_estimators: 나무의 개수 (공부할 학생 수)
# learning_rate: 오답을 얼마나 강력하게 반영할지
# max_depth: 나무의 깊이 (질문을 얼마나 복잡하게 던질지)
# 데이터가 적을 때 과적합을 막는 설정
rf = XGBClassifier(
    n_estimators=100,
    max_depth=5,    
    learning_rate=0.05,    
    subsample=0.8,         
    colsample_bytree=0.8,
    class_weight='balanced'
)


print("XGBoost training...")
rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\nAccuracy: {accuracy * 100:.2f}%")

print("\n[summary]")
print(classification_report(y_test, y_pred, target_names=le.classes_))

joblib.dump(rf, 'XGBoost.pkl')
joblib.dump(le, 'LableEncoder3.pkl')