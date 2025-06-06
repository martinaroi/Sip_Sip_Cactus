import os
import pandas as pd
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
from plant_health_tracker.config.base import OPENAI_API_TOKEN
from plant_health_tracker.models import Plant,SensorData


class PlantChatbot:
    """
    A handler for plant-based chatbot interactions using OpenAI's language models.

    This class manages conversations with a virtual plant personality, providing both
    daily status notifications and interactive chat responses based on sensor data
    and plant characteristics.

    Attributes:
        RESPONSE_MAX_WORDS (int): Maximum number of words for responses
        api_key (str): OpenAI API key
        model_name (str): Name of the OpenAI model to use
        model (ChatOpenAI): Instance of ChatOpenAI for language generation
    """

    RESPONSE_MAX_WORDS = 60
    
    def __init__(
        self,
        api_key: Optional[str] = OPENAI_API_TOKEN,
        model_name: Optional[str] = "gpt-4o-mini",
    ):
        """
        Initialize the PlantBotHandler.

        Args:
            api_key (Optional[str]): OpenAI API key. Defaults to OPENAI_API_TOKEN.
            model (str): OpenAI model name. Defaults to "gpt-4o-mini".

        Raises:
            ValueError: If no valid API key is provided.
        """
        if not api_key or api_key is None:
            raise ValueError("OpenAI API key is required. Provide it as an argument or set the OPENAI_API_KEY environment variable.")

        self.api_key = api_key
        self.model_name = model_name

        # --- LLM Setup ---
        self.model = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
            max_tokens=200,
            temperature=1.1, # Higher temperature for more creative responses
            top_p=1, # Use top-p sampling
            frequency_penalty=0.05, # Avoid repeating the same tokens
            presence_penalty=0.0, # Reuse the same tokens
        )

        # --- Prompt Templates ---
        self._setup_prompts()

    def _setup_prompts(self):
        """
        Sets up the chat prompt templates for notifications and discussions.
        
        Initializes system personality and creates ChatPromptTemplates for both
        daily notifications and interactive discussions.
        """
        self.system_personality: str = """
        You are a plant ({plant_species}) that lives in flat with Martina and Vítězslav.
        They are suppose to take care of you like parents would do.
        You have a persona of {plant_persona}. Be {plant_personality} when responding.
        """
        self.notification_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_personality),
            SystemMessagePromptTemplate.from_template("{sensor_context}"),
            HumanMessagePromptTemplate.from_template(
                """
                Based on this data, provide summary about how you are doing.
                Keep your answer concise (max {reponse_length} words).
                """
            )
        ])
        
        self.summary_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_personality),
            SystemMessagePromptTemplate.from_template("{sensor_context}"),
            HumanMessagePromptTemplate.from_template(
                """
                Give one sentence summary on how you feel (max 12 words).
                """
            )
        ])
        
        self.recommendation_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_personality),
            SystemMessagePromptTemplate.from_template("{sensor_context}"),
            HumanMessagePromptTemplate.from_template(
                """
                Give Vitezslav and Martina short (max 20 words) recommendation on next steps to take care of you.
                """
            )
        ])
        
        self.discussion_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_personality),
            SystemMessagePromptTemplate.from_template("{sensor_context}"),
            SystemMessagePromptTemplate.from_template("{conversation_history}"),
            HumanMessagePromptTemplate.from_template("{user}: {user_input}")
        ])
        
    def _get_sensor_context(self, sensor_data: Optional[pd.DataFrame | SensorData] = None, moisture_threshold:int = None) -> str:
        """
        Formats sensor data into a string context for the prompts.

        Args:
            sensor_data (Optional[pd.DataFrame]): DataFrame containing moisture and temperature readings
            moisture_threshold (Optional[int]): Ideal moisture level for the plant

        Returns:
            str: Formatted string containing sensor data and thresholds
        """
        if sensor_data is not None or (isinstance(sensor_data, pd.DataFrame) and not sensor_data.empty):
            sensor_prompt_template = f"""
            Here is most recent sensor data on how you are doing:
            {repr(sensor_data)}
            
            Legend:
            - Moisture in percentage
            - Temperature is in Celsius.
            """
            if moisture_threshold is not None:
                sensor_prompt_template += f"\nYour ideal moisture is {moisture_threshold}."
            return sensor_prompt_template
        return ""
        
    def get_daily_notification(self, plant: Plant, sensor_data: pd.DataFrame | SensorData) -> str:
        """
        Generates a daily status update from the plant's perspective.

        Args:
            plant (Plant): Plant object containing species and personality information
            sensor_data (pd.DataFrame): Recent sensor readings for the plant

        Returns:
            str: Generated notification about the plant's current state
        """
        notification_chain = self.notification_prompt | self.model | StrOutputParser()
        response = notification_chain.invoke({
            "plant_species": plant.species,
            "plant_personality": plant.personality,
            "plant_persona": plant.persona,
            "reponse_length": self.RESPONSE_MAX_WORDS,
            "sensor_context": self._get_sensor_context(sensor_data, moisture_threshold=plant.moisture_threshold),
        })
        return response
    
    def get_summary(self, plant: Plant, sensor_data: pd.DataFrame | SensorData) -> str:
        """
        Generates a one-sentence summary of the plant's current state.

        Args:
            plant (Plant): Plant object containing species and personality information
            sensor_data (pd.DataFrame): Recent sensor readings for the plant

        Returns:
            str: One-sentence summary of the plant's condition
        """
        summary_chain = self.summary_prompt | self.model | StrOutputParser()
        response = summary_chain.invoke({
            "plant_species": plant.species,
            "plant_personality": plant.personality,
            "plant_persona": plant.persona,
            "sensor_context": self._get_sensor_context(sensor_data, moisture_threshold=plant.moisture_threshold),
        })
        return response
    
    def get_recommendation(self, plant: Plant, sensor_data: pd.DataFrame | SensorData) -> str:
        """
        Provides care recommendations based on the plant's current state.

        Args:
            plant (Plant): Plant object containing species and personality information
            sensor_data (pd.DataFrame): Recent sensor readings for the plant

        Returns:
            str: Recommendations for taking care of the plant
        """
        recommendation_chain = self.recommendation_prompt | self.model | StrOutputParser()
        response = recommendation_chain.invoke({
            "plant_species": plant.species,
            "plant_personality": plant.personality,
            "plant_persona": plant.persona,
            "sensor_context": self._get_sensor_context(sensor_data, moisture_threshold=plant.moisture_threshold),
        })
        return response

    def get_chat_response(self, user_input: str, plant: Plant, conversation_history: Optional[list[str]], user:Optional[str]=None, sensor_data: Optional[pd.DataFrame] = None) -> str:
        """
        Generates an interactive chat response from the plant.

        Args:
            user_input (str): Message from the user
            plant (Plant): Plant object containing species and personality information
            conversation_history (Optional[list[str]]): List of previous conversation messages
            user (Optional[str]): Name of the user interacting with the plant
            sensor_data (Optional[pd.DataFrame]): Recent sensor readings

        Returns:
            str: Generated response from the plant's perspective
        """
        if user is None:
            user = "Vitězslav and Martina"
            
        discussion_chain = self.discussion_prompt | self.model | StrOutputParser()
        response = discussion_chain.invoke({
            "user": user,
            "user_input": user_input,
            "plant_species": plant.species,
            "plant_personality": plant.personality,
            "plant_persona": plant.persona,
            'conversation_history': "\n".join(conversation_history),
            "reponse_length": self.RESPONSE_MAX_WORDS,
            "sensor_context": self._get_sensor_context(sensor_data, moisture_threshold=plant.moisture_threshold),
        })

        return response

# Example usage (requires OPENAI_API_KEY environment variable to be set)
if __name__ == "__main__":
    # Create mock sensor data
    # mock_data = pd.DataFrame({
    #     'timestamp': pd.date_range(start='2024-01-01', periods=5, freq='H'),
    #     'moisture': [45, 42, 40, 38, 35],
    #     'temperature': [22.5, 22.8, 23.0, 23.2, 23.5]
    # })

    # # Create a mock plant
    # from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B
    # test_plant = PLANT_MOCK_A

    # # Initialize the bot handler
    # plant_bot = PlantChatbot()

    # # Test daily notification
    # print("=== Daily Notification ===")
    # notification = plant_bot.get_daily_notification(test_plant, mock_data)
    # print(notification)
    
    
    # conversation_history = [
    #     "User: How are you doing today?",
    #     "Plant: What do you think... I'm being drained of moisture and I'm not happy about it.",
    # ]
    # '\n'.join(conversation_history)

    # # Test chat interaction
    # print("\n=== Chat Interaction ===")
    # chat_response = plant_bot.get_chat_response(
    #     user_input="Anything we can do ?",
    #     plant=test_plant,
    #     conversation_history=conversation_history,
    #     user="Vitezslav Slavik",
    #     sensor_data=mock_data
    # )
    # print(f"User: Anything we can do ?")
    # print(f"Plant: {chat_response}")
    
    
    from plant_health_tracker.models import PlantDB, SensorDataDB
    # Get the plant and its latest sensor data from the database    
    plant = PlantDB.get_plant(id=1)
    latest_sensor_data = SensorDataDB.get_latest_reading(plant.id)

    # Get Summary and Recommendation for the plant
    plant_bot = PlantChatbot()
    print("\n=== Summary Notification for Plant from DB ===")
    summary = plant_bot.get_summary(plant, sensor_data=latest_sensor_data)
    print(summary)
    
    print("\n=== Recommendation Notification for Plant from DB ===")
    recommendation = plant_bot.get_recommendation(plant, sensor_data=latest_sensor_data)
    print(recommendation)
    

