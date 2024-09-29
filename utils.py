from typing import List
from openai import OpenAI
def get_chat_response(prompt, key, model="gpt-4o" ):
    client = OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "Your role is in translating Halachic texts is to provide direct translations without engaging in conversation or adding extra information. The interaction should be strictly limited to receiving Hebrew text and providing its English translation, reflecting the meaning of the original text as closely as possible."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content


def load_file():
    file_path = '/content/Arukh HaShulchan, Orach Chayim -- Wikisource.txt'

    # Open the file in read mode ('r')
    with open(file_path, 'r') as file:
        # Read the contents of the file into a variable
        file_contents = file.read()
    return file_contents


def iterative_text_splitter(text, max_size, separators):
    """
    Iteratively splits a text into a list of strings based on a list of separators,
    ensuring that each string does not exceed the specified maximum size.

    Parameters:
    - text (str): The original string to split.
    - max_size (int): The maximum allowed size for each chunk.
    - separators (list of str): A prioritized list of separators for splitting the text.

    Returns:
    - list of str: A list of strings, each not exceeding the maximum size.
    """
    # Initialize the list to hold the split strings.
    split_texts = []
    current_pos = 0
    if text == "":
        return ['']

    # Continue until the entire text is processed.
    while current_pos < len(text):
        # If the remainder of the text is within max_size, add it to the list and break.
        if len(text) - current_pos <= max_size:
            split_texts.append(text[current_pos:])
            break

        # Attempt to find a suitable split position using the separators.
        split_pos = -1
        for sep in separators:
            pos = text.rfind(sep, current_pos, current_pos + max_size + 1)
            if pos != -1:
                # Adjust the split position to include the separator at the end of the current chunk.
                split_pos = pos + len(sep)
                break

        # If no suitable separator-based split is found, split at max_size.
        if split_pos == -1 or split_pos < current_pos:
            split_pos = current_pos + max_size

        # Add the current chunk to the list and update the current position.
        split_texts.append(text[current_pos:split_pos])
        current_pos = split_pos

    return split_texts



def merge_file(chunks: List[str]) -> str:
    """
    Merge the given list of chunks into a single string.

    Args:
        chunks (List[str]): A list of strings representing the chunks.

    Returns:
        str: The merged string.
    """
    if chunks is None or len(chunks) == 0:
        return ''
    full = ''.join(chunks)
    return full