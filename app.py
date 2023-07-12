from flask import Flask, request, url_for, redirect, render_template
from flask_cors import CORS, cross_origin
import saspy
import matplotlib
# Matplotlib (a library for creating plots and graphs) expects to work with graphical user interfaces (GUIs).
# However, Flask runs in its own server thread, which is not the main thread of the application. This can cause
# issues because the GUI-related operations of Matplotlib are not compatible with Flask's thread.
matplotlib.use('Agg')  # Set the backend to Agg
import matplotlib.pyplot as plt
import io
import base64


app = Flask(__name__)

CORS(app)

# set up sas session, feed the macro code in it, get a pandas dataframe of the resulting data
def make_sas_data(macro):
    sas_session = saspy.SASsession()
    gpt_macro_submit = sas_session.submit("""                 
        %s
    """ % format(macro))
    gpt_plot_data_df = sas_session.sasdata2dataframe(table='y_values', libref='work')
    return gpt_plot_data_df

# make cpi graph
def make_cpi_graph(dataframe):
    x = dataframe['x']
    y = dataframe['y']
    plt.scatter(x, y, color='red', marker='o', facecolors='none')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Chat GPT Generated Macro')

    # Save the plot to a BytesIO object
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png', dpi=300)
    plt.close()

    # Encode the image data as base64
    image_stream.seek(0)
    base64_image = base64.b64encode(image_stream.getvalue()).decode('utf-8')

    return base64_image

@app.route('/')
def use_template():
    return render_template("index.html")


@app.route('/results',methods=['POST','GET'])
# obtain user input with request.form
def make_results():
    # polynomial_degree = request.form['1'] ---> this one worked for a while then it randomely stopped tf??
    # polynomial_degree = request.args.get('1', 'default_value') ---> works with postman, but not react form, since postman uses json or something
    polynomial_degree = request.form.get('1', 'default_value')

    # intentionally throw a 500 internal server error, for testing purposes
    # if polynomial_degree == 'error':
    #     raise Exception('Intentional backend error')

    # create a macro call based on the user input
    macro_call = f"%create_polynomial(degree={polynomial_degree})"

    # read the contents of the file to get the existing macro
    with open('macro.txt', 'r') as f:
        macro_code = f.read()

    # concatenate the existing macro and macro_call
    macro = macro_code + '\n' + macro_call

    # get the resulting pandas dataframe
    cpi_df = make_sas_data(macro)

    # make the cpi graph
    cpi_graph = make_cpi_graph(cpi_df)

    return render_template('result.html',pred=cpi_graph)

    # response = render_template('result.html',pred=f'This is the sas results: {polynomial_degree}')
    # for when testing error, correct user input will still generate an error, until page is refreshed. Here, I instruct the browser not to cache the response
    # response.headers['Cache-Control'] = 'no-cache' ---> didn't do shit- in fact its what threw an error
    
    # return response

if __name__ == '__main__':
    app.run(debug=True)


