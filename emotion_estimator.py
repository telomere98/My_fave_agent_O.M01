key = "07ab6dcf966841f7b30c548d4ca02529"
endpoint = "https://emotionestimatorbytextanalytics.cognitiveservices.azure.com/"

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

class EmotionEstimator:
    def authenticate_client(self):
        ta_credential = AzureKeyCredential(key)
        text_analytics_client = TextAnalyticsClient(
                endpoint=endpoint, 
                credential=ta_credential)
        return text_analytics_client

    def sentiment_analysis_example(self, client, input):
        documents = [input['utt']]
        response = client.analyze_sentiment(documents=documents,language="ja")[0]
        # print("Document Sentiment: {}".format(response.sentiment))
        # print("Overall scores: positive={0:.2f}; neutral={1:.2f}; negative={2:.2f} \n".format(
        #     response.confidence_scores.positive,
        #     response.confidence_scores.neutral,
        #     response.confidence_scores.negative,
        # ))
        result = ""
        for idx, sentence in enumerate(response.sentences):
            # print("Sentence: {}".format(sentence.text))
            # print("Sentence {} sentiment: {}".format(idx+1, sentence.sentiment))
            # print("Sentence score:\nPositive={0:.2f}\nNeutral={1:.2f}\nNegative={2:.2f}\n".format(
            #     sentence.confidence_scores.positive,
            #     sentence.confidence_scores.neutral,
            #     sentence.confidence_scores.negative,
            # ))
            result = result + "Sentence: {}".format(sentence.text) + "Sentence {} sentiment: {}".format(idx+1, sentence.sentiment) + "Sentence score:\nPositive={0:.2f}\nNeutral={1:.2f}\nNegative={2:.2f}\n".format(sentence.confidence_scores.positive, sentence.confidence_scores.neutral, sentence.confidence_scores.negative,
            )
        ee_result = "Document Sentiment: {}".format(response.sentiment) + "Overall scores: positive={0:.2f}; neutral={1:.2f}; negative={2:.2f} \n".format(response.confidence_scores.positive, response.confidence_scores.neutral, response.confidence_scores.negative) + result
        ee_result_fix = "posi={0:.2f}; n={1:.2f}; nega={2:.2f} \n".format(response.confidence_scores.positive, response.confidence_scores.neutral, response.confidence_scores.negative) #+ result
        return ee_result_fix