import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

import joblib
# data load
df = pd.read_csv('Mediapipe_ML_V6.csv')

#split csv data
x = df.iloc[:, :-1]
y = df.iloc[:, -1]

le = LabelEncoder()
y_encoded = le.fit_transform(y)  #One Hot Encoding
class_names = le.classes_ 

# 80% training 20% test, stratify, 
x_train, x_test, y_train, y_test = train_test_split(
    x, y_encoded, test_size=0.2, random_state=41, stratify=y_encoded
)

# Model
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=9,
    class_weight='balanced'
)
rf.fit(x, y_encoded)

# 5. 결과 평가
y_pred = rf.predict(x_test)

print(f"--- Accuracy : {accuracy_score(y_test, y_pred) * 100:.2f}% ---")
print("\n[summary]")
print(classification_report(y_test, y_pred, target_names=class_names))

joblib.dump(rf, 'RandomForest5.pkl')
#joblib.dump(le, 'LableEncoder3.pkl')

