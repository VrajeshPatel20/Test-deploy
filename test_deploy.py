import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import requests
from bs4 import BeautifulSoup


def get_dataset(url):
  
  response = requests.get(url)
  soup = BeautifulSoup(response.text, 'html.parser')

  html_table = soup.find_all('table', {'class': 'sortable plainrowheaders wikitable'})[0]  # Second table contains the data
  table_rows = html_table.find_all('tr')[1:]

  data = []
  for row in table_rows:
      cols = row.find_all(['th', 'td'])
      year = cols[0].text.strip()
      winner = cols[1].text.strip()
      score = cols[2].text.strip()
      runner_up = cols[3].text.strip()
      venue = cols[4].text.strip()
      location = cols[5].text.strip()
      attendence = cols[6].text.strip()
      # To ensure that data does not have nulls
      if attendence:
        data.append({
            'Year':year, 
            'Winner': winner, 
            'Score':score, 
            'Runner-Up':runner_up, 
            'Venue':venue, 
            'Location': location, 
            'Attendence': attendence
        })
  columns = ['Year', 'Winner','Score', 'Runner-Up', 'Venue', 'Location', 'Attendence']
  df = pd.DataFrame(data, columns=columns)
  df.replace({
          'Winner': {'West Germany': 'Germany'}, 
          'Runner-Up': {'West Germany': 'Germany'}
        }, 
      inplace=True
    )
  return df


app = dash.Dash(__name__)
server = app.server
wikipedia_url = "https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals"
df = get_dataset(wikipedia_url)

winner_counts = df.groupby("Winner")["Year"].count().reset_index()
winner_counts.columns = ["Country", "Wins"]

default_year = df['Year'][0]
default_country = winner_counts["Country"][0]

app.layout = html.Div([
    html.H1("FIFA World Cup Winners Dashboard",  style={'textAlign': 'center', 'fontSize': 40}),
    dcc.Graph(id='world-map'),
    
    html.P("Select a Country:", style={'fontSize': 20, "font-weight": "bold"}),
    dcc.Dropdown(
        id='country-list',
        options=[{'label': c, 'value': c} for c in winner_counts['Country']],
        value=default_country,
        clearable=False
    ),
    html.Div(id='total-wins', style={'textAlign': 'center'}),
    
    html.P("Select a Year:", style={'fontSize': 20}),
    dcc.Dropdown(
        id='year-list',
        options=[{'label': y, 'value': y} for y in df['Year']],
        value=default_year,
        clearable=False
    ),
    html.Div(id='yearly-result', style={'textAlign': 'center'})
])


@app.callback(
    Output('world-map', 'figure'),
    Input('country-list', 'value')
)
def create_choropleth_graph(country):
    fig = px.choropleth(
        winner_counts, 
        locations='Country', 
        locationmode='country names',
        color='Wins',
        title='World Cup Wins by Country',
        color_continuous_scale=px.colors.sequential.Plasma
    )
    fig.update_layout(
        geo=dict(
            showcoastlines=True,
            coastlinecolor="Black",
            showocean=True,
            oceancolor="lightblue"
        ),
        margin = {"r":0,"t":0,"l":0,"b":0}
    )
    return fig

@app.callback(
    Output('total-wins', 'children'),
    Input('country-list', 'value')
)
def total_wins(country):
    wins = winner_counts.loc[winner_counts['Country'] == country, 'Wins'].values[0]
    return html.H3(f"{country} has won the FIFA World Cup {wins} times")

@app.callback(
    Output('yearly-result', 'children'),
    Input('year-list', 'value')
)
def display_results(year):
    row = df[df['Year'] == year].iloc[0]
    return html.H3(f"Stats for FIFA world cup {year} -- Winner: {row['Winner']}, and Runner-Up: {row['Runner-Up']}")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
