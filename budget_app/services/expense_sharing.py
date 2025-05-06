# expense_sharing.py
# Provides logic for splitting expenses between multiple users (e.g., roommates)

def split_expense(amount, participants):
    """
    Splits the total expense among all participants.

    Args:
        amount (float): Total amount of the expense.
        participants (list): List of participant usernames/emails.

    Returns:
        dict: Mapping of participant to their share.
    """
    if not participants:
        return {}

    share = round(amount / len(participants), 2)
    return {participant: share for participant in participants}
