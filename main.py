from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify
from ariadne import gql, QueryType, MutationType, make_executable_schema, graphql_sync

# Define type definitions (schema) using SDL
type_defs = gql(
   """
   type Query {
        functions: [Function]
   }


   type Function {
        name: String!
        runtime: String!
    }  

   type Mutation {
        add_function(name: String!): Function
    }
   """
)

# Initialize query

query = QueryType()

# Initialize mutation

mutation = MutationType()

# Define resolvers

@query.field("functions")
def functions(*_):
   return [place.to_json() for place in Functions.query.all()]

# place resolver (add new  place)
@mutation.field("add_function")
def add_function(_, info, name):
   place = Functions(name=name)
   place.save()
   return place.to_json()

# Create executable schema
schema = make_executable_schema(type_defs, [query, mutation])

# ============ FLASK SECTION ============

# initialize flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Functions(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(80), nullable=False)

   def to_json(self):
       return {
           "name": self.name
       }

   def save(self):
       db.session.add(self)
       db.session.commit()

# Create a GraphQL Playground UI for the GraphQL schema
@app.route("/graphql", methods=["GET"])
def graphql_playground():
   # Playground accepts GET requests only.
   # If you wanted to support POST you'd have to
   # change the method to POST and set the content
   # type header to application/graphql
   return PLAYGROUND_HTML

# Create a GraphQL endpoint for executing GraphQL queries
@app.route("/graphql", methods=["POST"])
def graphql_server():
   data = request.get_json()
   success, result = graphql_sync(schema, data, context_value={"request": request})
   status_code = 200 if success else 400
   return jsonify(result), status_code

# Run the app
if __name__ == "__main__":
   app.run(debug=True)
