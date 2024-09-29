import streamlit as st
import openai
import pandas as pd
import csv
import os
import time
import json
import chardet

import utils
from utils import iterative_text_splitter

# Placeholder for OpenAI API key
api_key = "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"


# Function to process a single string with improved error handling
def process_string(input_string):
    try:
        result = utils.get_chat_response(input_string, api_key)
        return {"input": input_string, "output": result, "error": ""}
    except openai.error.APIError as e:
        return {"input": input_string, "output": "", "error": f"API Error: {str(e)}"}
    except openai.error.RateLimitError as e:
        return {"input": input_string, "output": "", "error": f"Rate Limit Error: {str(e)}"}
    except Exception as e:
        return {"input": input_string, "output": "", "error": f"Unexpected Error: {str(e)}"}


# Function to save progress to CSV
def save_progress(results, filename):
    results.to_csv(filename, index=False)


# Function to load progress from CSV
def load_progress(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=["Input", "Output", "Error"])


# Function to save processing state
def save_state(filename, state):
    with open(filename, 'w') as f:
        json.dump(state, f)


# Function to load processing state
def load_state(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {"processing": False, "current_index": 0}


def detect_encoding(file_content):
    result = chardet.detect(file_content)
    return result['encoding']


def main():
    st.title("OpenAI API Processor")

    # File uploader
    uploaded_file = st.file_uploader("Choose a text file", type="txt")
    if uploaded_file is not None:
        # Generate unique filenames for this session
        session_id = uploaded_file.name.split('.')[0]
        progress_file = f"{session_id}_progress.csv"
        state_file = f"{session_id}_state.json"

        # Load existing progress and state
        st.session_state["results"] = load_progress(progress_file)
        state = load_state(state_file)
        st.session_state.processing = state["processing"]
        current_index = state["current_index"]

        # Detect file encoding
        file_content = uploaded_file.read()
        file_encoding = detect_encoding(file_content)
        st.write(f"Detected file encoding: {file_encoding}")

        # Reset file pointer
        uploaded_file.seek(0)

        # Read file with detected encoding
        try:
            file_content = file_content.decode(file_encoding)
        except UnicodeDecodeError:
            st.error(
                f"Failed to decode the file with {file_encoding} encoding. Please try a different file or encoding.")
            return

        strings_list = iterative_text_splitter(file_content, 3000, ['\n\n', '\n', '.', ',', ' '])

        # Display the chunks to be processed
        total_strings = len(strings_list)
        st.write(f"Total strings to be processed: {total_strings}")

        # Create placeholders for updating progress
        progress_text = st.empty()
        progress_bar = st.progress(0)

        # Update initial progress
        progress_text.text(f"Current progress: {current_index}/{total_strings}")
        progress_bar.progress(current_index / total_strings)

        # Button to start/pause processing
        if st.button("Start/Pause Processing"):
            st.session_state.processing = not st.session_state.processing
            save_state(state_file, {"processing": st.session_state.processing, "current_index": current_index})

        # Display current state
        st.write(f"Processing is currently: {'Active' if st.session_state.processing else 'Paused'}")

        # Process strings
        for i in range(current_index, total_strings):
            # Check if processing should continue
            if not st.session_state.processing:
                st.write("Processing paused. Click 'Start/Pause Processing' to resume.")
                break

            input_string = strings_list[i]
            if input_string not in st.session_state["results"]["Input"].values:
                result = process_string(input_string)
                new_row = pd.DataFrame(
                    [{"Input": result["input"], "Output": result["output"], "Error": result["error"]}])
                st.session_state["results"] = pd.concat([st.session_state["results"], new_row], ignore_index=True)

                # Save progress after each processed string
                save_progress(st.session_state["results"], progress_file)

                # Update the display
                st.write(f"Processed: {input_string[:50]}...")

                # Update progress bar and state
                current_index = i + 1
                progress_text.text(f"Current progress: {current_index}/{total_strings}")
                progress_bar.progress(current_index / total_strings)
                save_state(state_file, {"processing": st.session_state.processing, "current_index": current_index})

                # Add a small delay to allow for interruption
                time.sleep(0.1)

        # Display results in a table
        st.write("Results:")
        st.dataframe(st.session_state["results"])

        # Retry failed requests
        failed_inputs = st.session_state["results"][st.session_state["results"]["Error"] != ""]
        for index, row in failed_inputs.iterrows():
            if st.button(f"Retry: {row['Input'][:50]}..."):
                result = process_string(row["Input"])
                st.session_state["results"].loc[index] = [result["input"], result["output"], result["error"]]
                save_progress(st.session_state["results"], progress_file)


if __name__ == "__main__":
    main()