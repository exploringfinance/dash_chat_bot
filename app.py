###########################
# Author: Tony Trevisan
# Website: www.altanalyticsllc.com
# Date: 2023-10-14
# File: app.py (dash_chat_bot)
# Description: Chat bot that allows a user to upload PDF/TXT files
# Notes: 
###########################

# pip install -r requirements.txt

# Load libraries
import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import boto3
import json
import base64
import io
import os
import PyPDF2


# Set the AWS credentials file
credentials_file_path = 'assets/credentials'
os.environ['AWS_SHARED_CREDENTIALS_FILE'] = credentials_file_path

# Create app with dbc theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN]) # SANDSTONE


# Read in the initial/silly prompt in assets folder
silly_prompt = 'assets/silly_prompt.txt'
with open(silly_prompt, 'r') as file:
    silly_prompt = file.read()


# Set the user code based on file so not embedded
user_code = 'assets/user_code.txt'
with open(user_code, 'r') as file:
    user_code = file.read()
code_expected = user_code.strip()

# Function to read in PDF file
def extract_text_from_pdf(contents):
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Create a PdfFileReader object
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(decoded))

        # Extract text from each page
        text = ""
        for page_number in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_number].extract_text()

        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return "Error extracting text"



# Create text for the app in Markdown format
md_style = {'width': '80%', 'font-size':'14px'}
md_initial = """
Welcome to the ALT Analytics LLM demo. The application is built in Python Dash and is connected
to the Anthropic Claude 2 model using AWS Bedrock. The objective of the app is to give a user interface
to interact with the LLM without having to go through the AWS console. Furthermore, it gives
users the ability to upload PDF or TXT documents before asking their question. For example,
you can upload a PDF document and then ask the LLM to summarize it for you ro check for grammar. 

To enable the app, **you must have a code**. Reach out to 
[tony@altanalyticsllc.com](mailto:tony@altanalyticsllc.com) to get the code or 
else none of the features will work.The user has the ability to enable "Silly Mode" for the app. This 
will usually generate false and funny answers. If the app
is in "Silly Mode", you should not take seriously any of the output from the model. If you would like 
to know how you can build a similar model on your own, you can follow the instructions laid out in 
[this article]().
"""
md_instructions = dcc.Markdown(children = md_initial, style = md_style, 
                              dangerously_allow_html=True) 
                              
md_upload = """
Use the buttons below to upload a TXT or PDF file that will be included in the initial prompt. 
**You have to upload the files before making an initial prompt** or it will not work. If the text 
is in Microsoft Word, then you will need to save/export the file as a .txt file before uploading. 
If you have already made an initial request, then you will need to press "Reset" and start over 
in order for your PDF/TXT files to be included. 

"""
md_upload_ins = dcc.Markdown(children = md_upload, style = md_style, 
                              dangerously_allow_html=True) 
                              
md_prompt = """
When entering your prompt, be clear about what you are asking and what your response should look like.
If asking the LLM to summarize or review a document. Upload the document and then enter the prompt: 
"Can you summarie the text above" or "Are there and gramatical mistakes in the text above". Be sure to 
reference the "Text above" because that is the order the text is entered. It's best to experiment. 
If you continue asking without refreshing the page, the model will ingest all the correspondance. 
This means, follow-up questions do not have to be as specific. *Enjoy and have fun*!
"""
md_prompt_ins = dcc.Markdown(children = md_prompt, style = md_style, 
                              dangerously_allow_html=True) 

# Set application layout
app.layout = html.Div([
  # Top navigation bar
  dbc.Nav(
    children = [dbc.NavLink('ALT Analytics LLM Demo',href = 'https://www.altanalyticsllc.com',
                style = {'color': 'white', 'font-size':'20px'})],
                class_name = 'bg-primary', style = {'height': '65px', 'line-height':'45px'}, 
                pills = True),
  dbc.Container([

  # Initial instructions
  html.Div(children = [
    html.Br(),
    html.H4("LLM Powered by AWS and Claude 2 from Anthropic"),
    md_instructions,
    dbc.Row([dbc.Col(dbc.Input(id='code-input', placeholder = 'Enter the code to enable the app', 
                              type = 'text'),width = 4),
             ]),
    html.Br(),
    
    # Upload document section
    md_upload_ins,
    dbc.Row([dbc.Col(dcc.Upload(id='upload-pdf',multiple=False,
                        children=dbc.Button('Upload PDF', id='upload_pdf_doc', color = 'info')),
                        
                        width=4),
             dbc.Col(dcc.Upload(id='upload-text',multiple=False,
                        children=dbc.Button('Upload txt', id='upload_txt_doc', color = 'info')),
                        
                        width=4),
             dbc.Col(dbc.RadioItems(
             options=[
                {"label": "Normal Mode", "value": 1},
                {"label": "Silly Mode", "value": 2}],value=1,
                id="silly-input",), width = 4)]),
    dbc.Row([dbc.Col(html.Div(id='upload-pdf-display'),width = 4),
             dbc.Col(html.Div(id='upload-txt-display'),width = 4)]),

    dcc.Store(id='upload-txt-content'),
    dcc.Store(id='upload-pdf-content'),
    
    # Section with the prompt
    html.Hr(),
    md_prompt_ins,
     html.Div(id='question-display'),
     dcc.Store(id = 'prompt-store'),
     dbc.Spinner(html.Div(id='loading-output-chat'), color = "warning"),
     dbc.Row([dbc.Col(dbc.Input(id='question-input', placeholder = 'Enter your prompt here', type = 'text'), width = 8),
              dbc.Col(dbc.Button('Go', id = 'submit-button', color = 'success'), width = 1),
              dbc.Col(dbc.Button('Reset', id = 'reset-button', color = 'warning'), width = 2)]),
   html.Br(),
   html.Br(),
   
   # Bottom nav bar
   html.Div(dbc.NavbarSimple(
    children = [dbc.NavLink('Source Code',href = 'https://github.com/exploringfinance/dash_chat_bot',
                style = {'color': 'white', 'font-size':'12px'})],
                style = {'height': '45px'}, 
                color = 'primary', fixed = 'bottom',
  ))]),
])])


# This is used to replace the raw text output to make it more readable
human = """  

<u>*You*</u>:  
  
"""
assistant = """  

*[Claude2](https://www.anthropic.com/index/claude-2):*  

"""

# Callback to read in text file
@app.callback(Output('upload-txt-content', 'data'),
              Output('upload-txt-display', 'children'),
              Input('code-input','value'),
              Input('upload-text', 'contents'),
              State('upload-text', 'filename'))
def upload_text_file(code, contents, filename):
    
     # Check for code
     if code != code_expected:
        print('No code')
        return '', html.P('Please enter the valid code')
    
     if contents is not None:
        # Validate file type
        if filename.lower().find('.txt') == -1:
          return '', html.P('File was not a .txt file')
        
        # Read in data
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file_contents = io.StringIO(decoded.decode('ISO-8859-1')).read()
        return file_contents, html.P('txt file: ' + filename + ' uploaded and received')
     return '', html.P('No txt File uploaded')


# Read in PDF File
@app.callback(Output('upload-pdf-content', 'data'),
              Output('upload-pdf-display', 'children'),
              Input('code-input','value'),
              Input('upload-pdf', 'contents'),
              State('upload-pdf', 'filename'))
def upload_pdf_file(code, contents, filename):
  
    # Check for App Code
    if code != code_expected:
      print('No code')
      return '', html.P('Please enter the valid code')
    
    if contents is not None:
        # Check file type
        if filename.lower().find('.pdf') == -1:
          return '', html.P('File was not a .pdf file')
        
        # Read in text from PDF
        pdf_text = extract_text_from_pdf(contents)
        # print(pdf_text)
        return pdf_text, html.P('PDF file: ' + filename + ' uploaded and received')
    return '', html.P('No PDF File uploaded')


# Main callback that generates the model output
@app.callback(Output('loading-output-chat', 'children'),
              Output('question-display', 'children'),
              Output('prompt-store', 'data'),
              Output('question-input', 'value'),
              Output('submit-button', 'n_clicks'),
              Output('reset-button', 'n_clicks'),
              Input('submit-button', 'n_clicks'),
              Input('reset-button', 'n_clicks'),
              State('question-input', 'value'),
              State('prompt-store', 'data'),
              State('silly-input', "value"),
              State('upload-txt-content', 'data'),
              State('upload-pdf-content', 'data'),
              State('code-input','value'),
              prevent_initial_call=True)
def execute_model(n_clicks, r_clicks, input_value, existing_prompt, silly,
                  upload_txt_content, upload_pdf_content, code):
  
  # Print r_clicks and n_clicks
  print(n_clicks)
  print(r_clicks)
  
  # Check if application code was entered
  if code != code_expected:
    print('No code')
    return "", "Please enter the proper code", "", "", None, None 
  
  # Reset application
  if r_clicks is not None:
    print('Reset')
    return "", "", "", "", None, None 
  
  # Determine whether to make prompt silly or not by using text fil
  initial_prompt = ''
  if silly == 2:
    initial_prompt = silly_prompt
  print(initial_prompt)
  
  # Connect to bedrock
  session = boto3.Session()
  bedrock = session.client(service_name = 'bedrock-runtime', region_name = 'us-east-1')
  
  # Determine which prompt to create
  if n_clicks is None:
    return "", "", "", "", None, None 
  # This builds the initial prompt that will start the chat chain
  elif n_clicks == 1:
    claude_prompt = 'Human: ' + initial_prompt + '\n' + upload_txt_content + '\n' +\
    upload_pdf_content + '\n' + input_value + '\nAssistant:'
  # This adds to the existing prompt
  else:
    claude_prompt = existing_prompt + 'Human:' + input_value + 'Assistant:'
  
  # Commented out to keep from Logging user interactions
  # print('Prompt:')
  # print(claude_prompt)
  body = json.dumps({
    "prompt": claude_prompt,
    "max_tokens_to_sample": 1000,
    "temperature": 0.1,
    "top_p": 0.9,
  })
  
  # Create API request to the model
  modelId = 'anthropic.claude-v2'
  accept = 'application/json'
  contentType = 'application/json'
  response = bedrock.invoke_model(body = body, modelId = modelId, accept = accept, contentType = contentType)
  response_body = json.loads(response.get('body').read())
  claude_prompt = claude_prompt + response_body.get('completion')
  
  # Format output for display in markdown
  output_formatted = claude_prompt.replace('Human:', human)
  output_formatted = output_formatted.replace('Assistant:', assistant)
  output_formatted = output_formatted.replace(upload_txt_content, '')
  output_formatted = output_formatted.replace(upload_pdf_content, '')
  md_text = dcc.Markdown(children = output_formatted, style = md_style, 
                         dangerously_allow_html=True) #'<b>bold</b> <u>underline</u>')
                         
  # Return formatted text and raw text
  return "", md_text, claude_prompt, "", n_clicks, None


if __name__ == '__main__':
    app.run_server(debug=True)

