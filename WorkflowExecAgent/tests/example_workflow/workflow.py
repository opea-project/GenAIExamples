# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier


def churn_prediction(params):
    df = pd.read_csv("./WA_Fn-UseC_-Telco-Customer-Churn.csv")

    # Data Cleaning
    df = df.drop(["customerID"], axis=1)
    select_cols = ["gender", "tenure", "MonthlyCharges", "TotalCharges", "Churn"]
    df = df[select_cols]

    df["TotalCharges"] = pd.to_numeric(df.TotalCharges, errors="coerce")
    df.drop(labels=df[df["tenure"] == 0].index, axis=0, inplace=True)
    df.fillna(df["TotalCharges"].mean())

    # Data Preprocessing
    encoders = {}

    def object_to_int(dataframe_series):
        if dataframe_series.dtype == "object":
            encoders[dataframe_series.name] = LabelEncoder().fit(dataframe_series)
            dataframe_series = encoders[dataframe_series.name].transform(dataframe_series)
        return dataframe_series

    df = df.apply(lambda x: object_to_int(x))
    X = df.drop(columns=["Churn"])
    y = df["Churn"].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=40, stratify=y)

    model_scores = []

    models = [
        (
            "Random Forest",
            RandomForestClassifier(random_state=42),
            {"model__n_estimators": [50, 100, 200], "model__max_depth": [None, 10, 20]},
        ),  # Add hyperparameters for Random Forest
        (
            "Gradient Boosting",
            GradientBoostingClassifier(random_state=42),
            {"model__n_estimators": [50, 100, 200], "model__learning_rate": [0.05, 0.1, 0.5]},
        ),  # Add hyperparameters for Gradient Boosting
        (
            "Support Vector Machine",
            SVC(random_state=42, class_weight="balanced"),
            {"model__C": [0.1, 1, 10], "model__gamma": ["scale", "auto"]},
        ),  # Add hyperparameters for SVM
        (
            "Logistic Regression",
            LogisticRegression(random_state=42, class_weight="balanced"),
            {"model__C": [0.1, 1, 10], "model__penalty": ["l1", "l2"]},
        ),  # Add hyperparameters for Logistic Regression
        (
            "K-Nearest Neighbors",
            KNeighborsClassifier(),
            {"model__n_neighbors": [3, 5, 7], "model__weights": ["uniform", "distance"]},
        ),  # Add hyperparameters for KNN
        (
            "Decision Tree",
            DecisionTreeClassifier(random_state=42),
            {"model__max_depth": [None, 10, 20], "model__min_samples_split": [2, 5, 10]},
        ),  # Add hyperparameters for Decision Tree
        (
            "Ada Boost",
            AdaBoostClassifier(random_state=42),
            {"model__n_estimators": [50, 100, 200], "model__learning_rate": [0.05, 0.1, 0.5]},
        ),  # Add hyperparameters for Ada Boost
        (
            "XG Boost",
            XGBClassifier(random_state=42),
            {"model__n_estimators": [50, 100, 200], "model__learning_rate": [0.05, 0.1, 0.5]},
        ),  # Add hyperparameters for XG Boost
        ("Naive Bayes", GaussianNB(), {}),  # No hyperparameters for Naive Bayes
    ]

    best_model = None
    best_accuracy = 0.0

    for name, model, param_grid in models:
        # Create a pipeline for each model
        pipeline = Pipeline([("scaler", MinMaxScaler()), ("model", model)])  # Feature Scaling

        # Hyperparameter tuning using GridSearchCV
        if param_grid:
            grid_search = GridSearchCV(pipeline, param_grid, cv=2)
            grid_search.fit(X_train, y_train)
            pipeline = grid_search.best_estimator_

        # Fit the pipeline on the training data
        pipeline.fit(X_train, y_train)

        # Make predictions on the test data
        y_pred = pipeline.predict(X_test)

        # Calculate accuracy score
        accuracy = accuracy_score(y_test, y_pred)

        # Append model name and accuracy to the list
        model_scores.append({"Model": name, "Accuracy": accuracy})

        # Convert the list to a DataFrame
        scores_df = pd.DataFrame(model_scores)
        print("Model:", name)
        print("Test Accuracy:", round(accuracy, 3), "%\n")

        # Check if the current model has the best accuracy
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = pipeline

    # Retrieve the overall best model
    print("Best Model:")
    print("Test Accuracy:", best_accuracy)
    print("Model Pipeline:", best_model, "with accuracy", round(best_accuracy, 2), "%\n")

    # Process and Predict input values from user
    def transform_params(name, value):
        return encoders[name].transform(value)[0]

    predict_input = {}
    print("Predicting with user provided params:", params)
    for key, value in params.items():
        if key in encoders.keys():
            predict_input[key] = transform_params(key, [value])
        else:
            predict_input[key] = value

    predict_input = pd.DataFrame([predict_input])
    result = best_model.predict(predict_input)
    params["prediction"] = encoders["Churn"].inverse_transform(result)[0]
    result = json.dumps(params)

    return result


def run_workflow(params):
    return churn_prediction(params)
