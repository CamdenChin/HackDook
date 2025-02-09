import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('punkt')
nltk.download('stopwords')

filename =  'example_lesson_plan.txt'

str = open(filename, 'r').read()

def extract_keywords(str, num_keywords=20):
    """
    Extracts keywords from a paragraph using TF-IDF.

    Args:
        paragraph (str): The input paragraph.
        num_keywords (int): The number of keywords to extract.

    Returns:
        list: A list of extracted keywords.
    """
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(str.lower())
    filtered_tokens = [w for w in word_tokens if not w in stop_words and w.isalnum()]

    vectorizer = TfidfVectorizer()
    vectorizer.fit([str])
    tfidf_vector = vectorizer.transform([' '.join(filtered_tokens)])

    feature_array = vectorizer.get_feature_names_out()
    tfidf_sorting = tfidf_vector.toarray().flatten().argsort()[::-1]

    top_n = feature_array[tfidf_sorting][:num_keywords]
    return list(top_n)

if __name__=="__main__":
    keywords = extract_keywords(str)
    print(keywords)