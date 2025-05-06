# ml_utils.py

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle

# Pre-trained categories for demonstration
sample_data = [
    ("Uber ride", "Transport"),
    ("Electric bill", "Utilities"),
    ("Pizza", "Food"),
    ("Movie ticket", "Entertainment"),
    ("Salary from job", "Income"),
    ("Medicine", "Health")
]

# Train the classifier (can be expanded later or loaded from a file)
def train_model():
    """
    Train a Naive Bayes classifier on sample keyword-category data.
    Saves the model and vectorizer to disk.
    """
    texts, labels = zip(*sample_data)
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(texts)
    
    model = MultinomialNB()
    model.fit(X, labels)

    # Save model and vectorizer
    with open("model.pkl", "wb") as f:
        pickle.dump((model, vectorizer), f)

# Predict category based on description
def predict_category(description):
    """
    Predict the category of an expense using the trained model.

    Parameters:
        description (str): Expense description (e.g., "Bought burger")

    Returns:
        str: Predicted category or 'Other' if model not found
    """
    try:
        # Load model and vectorizer
        with open("model.pkl", "rb") as f:
            model, vectorizer = pickle.load(f)
        
        X = vectorizer.transform([description])
        return model.predict(X)[0]
    except FileNotFoundError:
        return "Other"

# Only train when run directly
if __name__ == "__main__":
    train_model()
