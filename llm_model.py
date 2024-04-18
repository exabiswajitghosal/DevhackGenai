import json
import os
import boto3
from openai import OpenAI
from langchain.vectorstores.chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

openai_api = os.getenv("OPENAI_API_KEY")
aws_bucket = os.getenv("S3_BUCKET_NAME")
aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_access = os.getenv("AWS_ACCESS_KEY_ID")
s3 = boto3.client('s3', aws_access_key_id=aws_access, aws_secret_access_key=aws_secret)

PROMPT_TEMPLATE = """
Answer the question based only on the following context don't give reference:
{context}
---
Answer the question based on the above context : {question}
"""


def generate_content_from_documents(category=None, industry=None, age=None, zip_code=None, state=None,
                                    claims_data=None):
    prefix = f"{category}/"
    if category == "regulations":
        query_text = '''Give me the regulatory details for Construction industry in the state of California.
                    Please provide the details like in the examples below. Provide output with atleast 5 regulatory 
                    details in bullet points.
                    example 1:
                    Regulation : Title 9. Section 1538. Rock Drilling Operations.
                    Details    : When drilling holes in rock, or other dust-producing material, the dust shall be controlled 
                                within the maximum acceptable concentrations set forth in Section 5208 (asbestos) and 
                                Section 5155 (silica and silicates) of the General Industry Safety Orders.
                                 Respiratory protection may be acceptable; refer to Article 4, Sections 1530 and 1531.
                    example 2:
                    Regulation : title 8, section 3203
                    Details    : Employer must have a written and effective Injury and Illness Prevention Program (IIPP)
                                meeting the requirements of California Code of Regulations '''
    else:
        query_text = '''Give me the Safety tips for Constructions industry for the state California. 
                    Provide details regarding Safety Communications, Planning, rules, training and prevention programs.
                    The details can be as specific as required for the construction industry on Lifting techniques,
                    Tool maintenance, communication methods, “to do” lists, checklists, safety or training courses etc.
                    Provide the details in 10 bullets points, limit each bullet point to 2 lines.'''
    chroma_path = f"./chroma/{prefix}"
    # Prepare the DB.
    embedding_function = OpenAIEmbeddings(openai_api_key=openai_api)
    db = Chroma(persist_directory=chroma_path, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    if len(results) == 0 or results[0][1] < 0.7:
        return None
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    model = ChatOpenAI()
    response_text = model.predict(prompt)
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    if not response_text:
        return None
    formatted_source = []
    for source in sources:
        url = "/".join(source.split("/")[3:])
        formatted_url = f"https://mygenaidevhack.s3.amazonaws.com/{url}"
        if formatted_url not in formatted_source:
            formatted_source.append(formatted_url)
    formatted_response = json.dumps({
        "category": category,
        "response": response_text,
        "sources": formatted_source,
        "industry": industry,
        "state": state,
        "date": datetime.now().date().strftime("%Y-%m-%d")
    })
    # s3.put_object(Bucket=aws_bucket, Key=f"archive/{prefix}{datetime.now()}.json", Body=formatted_response)
    if response_text is not None:
        return formatted_response
    return None


def generate_content(weather_data=None):
    # prompt = f"{weather_data} give me the key points in bullets points only about weather data"
    prompt = (f" Please summarize the weather data that is in JSON format delimited with triple backticks"
              f" '''{weather_data}''' in bullet points with details of "
              f"Event Type,Severity, ,Effective Time,Impact,Location(1st)")
    client = OpenAI(api_key=openai_api)
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        temperature=0,
        max_tokens=100,
    )
    return response.choices[0].text
