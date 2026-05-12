class SubmissionIntelAdapter:
    """
    Compatibility and Intelligence layer for the Evaluation OS.
    Decouples the UI and Engines from the raw JSON schema.
    """

    @staticmethod
    def get_similarity_score(submission):
        """Extracts the numeric similarity score from fraud signals."""
        if not submission.fraud_signals:
            return 0.0
        
        # Handle cases where it might be stored as a string with '%' or a float
        val = submission.fraud_signals.get("content_similarity", 0)
        if isinstance(val, str):
            try:
                return float(val.replace('%', ''))
            except ValueError:
                return 0.0
        return float(val)

    @staticmethod
    def get_ai_probability(submission):
        """Extracts AI probability from analysis signals."""
        if not submission.ai_analysis:
            return 0.0
        
        val = submission.ai_analysis.get("ai_pattern_match", 0)
        if isinstance(val, str):
            try:
                return float(val.replace('%', ''))
            except ValueError:
                return 0.0
        return float(val)

    @staticmethod
    def get_learning_signal(submission, key, default="N/A"):
        """Safely retrieves specific learning metrics."""
        return submission.learning_signals.get(key, default)
