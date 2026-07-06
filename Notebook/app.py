from flask import Flask

app = Flask(__name__)

@app.route("/")
def dashboard():
    return """
    <html>
    <head>
        <title>Electricity Consumption Dashboard</title>
    </head>

    <body>

    <h2>Electricity Consumption Analysis (2019–2020)</h2>

    <div class='tableauPlaceholder' id='viz'>
        <object class='tableauViz' width='100%' height='800'>
            <param name='host_url' value='https://public.tableau.com/' />
            <param name='embed_code_version' value='3' />
            <param name='name' value='electricity-dashboard/Story1' />
            <param name='tabs' value='no' />
            <param name='toolbar' value='yes' />
        </object>
    </div>

    <script src="https://public.tableau.com/javascripts/api/viz_v1.js"></script>

    </body>
    </html>
    """

if __name__ == "__main__":

    app.run(debug=True)
