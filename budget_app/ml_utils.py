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
    import os
    # Train model if it doesn't exist
    if not os.path.exists("model.pkl"):
        train_model()
    
    try:
        # Load model and vectorizer
        with open("model.pkl", "rb") as f:
            model, vectorizer = pickle.load(f)
        
        X = vectorizer.transform([description])
        return model.predict(X)[0]
    except (FileNotFoundError, Exception) as e:
        # Fallback to simple keyword matching if ML fails
        description_lower = description.lower()
        if any(word in description_lower for word in ['food', 'restaurant', 'pizza', 'burger', 'meal', 'grocery']):
            return "Food"
        elif any(word in description_lower for word in ['uber', 'taxi', 'transport', 'bus', 'train', 'gas']):
            return "Transport"
        elif any(word in description_lower for word in ['electric', 'water', 'utility', 'bill', 'internet']):
            return "Utilities"
        elif any(word in description_lower for word in ['movie', 'entertainment', 'game', 'concert']):
            return "Entertainment"
        elif any(word in description_lower for word in ['medicine', 'doctor', 'health', 'pharmacy']):
            return "Health"
        else:
            return "Other"

# Only train when run directly
if __name__ == "__main__":
    train_model()
