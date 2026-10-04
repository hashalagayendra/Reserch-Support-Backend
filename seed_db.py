import sys
import os
import uuid

# Add the project root to the sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, engine
from app.db.models import Base, User, Project, AITool, ApiKey

def seed_database():
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they did not already exist).")
    
    db = SessionLocal()
    try:
        users_data = [
            {"email": "user1@example.com", "password": "hash1", "project_name": "Project Alpha"},
            {"email": "user2@example.com", "password": "hash2", "project_name": "Project Beta"}
        ]
        
        projects = []

        for ud in users_data:
            # Check if dummy user exists
            user = db.query(User).filter(User.email == ud["email"]).first()
            if not user:
                user = User(email=ud["email"], hashed_password=ud["password"])
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"Created user with ID: {user.id} ({user.email})")
            else:
                print(f"User already exists with ID: {user.id} ({user.email})")

            # Check if dummy project exists for this user
            project = db.query(Project).filter(Project.name == ud["project_name"], Project.user_id == user.id).first()
            if not project:
                project = Project(user_id=user.id, name=ud["project_name"])
                db.add(project)
                db.flush()
                # Create an API key for the project
                new_api_key = ApiKey(project_id=project.id, key_value=f"sk-dummy-{uuid.uuid4().hex[:8]}")
                db.add(new_api_key)
                
                db.commit()
                db.refresh(project)
                print(f"Created project '{project.name}' with ID: {project.id} and API Key '{new_api_key.key_value}'")
            else:
                print(f"Project '{project.name}' already exists with ID: {project.id}")
            
            projects.append(project)

        # Actual Tools we can use
        tools_data = [
            {
                "tool_title": "get_current_weather",
                "description": "Fetches the current weather for a given latitude and longitude using Open-Meteo API.",
                "argument": {"latitude": "float", "longitude": "float", "current_weather": "true"},
                "api_url": "https://api.open-meteo.com/v1/forecast",
                "http_method": "GET",
                "headers": {}
            },
            {
                "tool_title": "get_random_joke",
                "description": "Fetches a random joke.",
                "argument": {},
                "api_url": "https://official-joke-api.appspot.com/random_joke",
                "http_method": "GET",
                "headers": {}
            },
            {
                "tool_title": "get_cat_fact",
                "description": "Fetches a random fact about cats.",
                "argument": {},
                "api_url": "https://catfact.ninja/fact",
                "http_method": "GET",
                "headers": {}
            },
            {
                "tool_title": "get_gender_by_name",
                "description": "Predicts the gender of a person based on their first name.",
                "argument": {"name": "string"},
                "api_url": "https://api.genderize.io",
                "http_method": "GET",
                "headers": {}
            }
        ]

        # Add tools to both projects
        for project in projects:
            for tool_info in tools_data:
                existing_tool = db.query(AITool).filter(
                    AITool.tool_title == tool_info["tool_title"], 
                    AITool.project_id == project.id
                ).first()

                if not existing_tool:
                    new_tool = AITool(
                        project_id=project.id,
                        tool_title=tool_info["tool_title"],
                        description=tool_info["description"],
                        argument=tool_info["argument"],
                        api_url=tool_info["api_url"],
                        http_method=tool_info["http_method"],
                        headers=tool_info["headers"]
                    )
                    db.add(new_tool)
                    print(f"Added tool: {tool_info['tool_title']} to project '{project.name}'")
                else:
                    print(f"Tool {tool_info['tool_title']} already exists in project '{project.name}'.")

        db.commit()
        print("Database seeding completed!")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
