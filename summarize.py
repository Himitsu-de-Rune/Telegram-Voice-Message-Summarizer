from transformers import pipeline

def summarize(text: str) -> str:
    summarizer = pipeline("summarization", model="cointegrated/rut5-base-multitask")
    summary = summarizer(text, max_length=100, min_length=1, do_sample=False)

    return(summary[0]['summary_text'])
