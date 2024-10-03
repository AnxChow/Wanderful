from transformers import AutoModelForCausalLM, AutoTokenizer
import re

# TODO fix the prompting test out different models - it's really bad rn

class CommunicationAgent:
    def __init__(self, model_name="EleutherAI/gpt-neo-125M"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.conversation_memory = {}  # Store parsed variables here (destination, dates, preferences)
        print(f"Loaded model {model_name} for natural conversation.")

    def generate_response(self, prompt):
        # Encode the prompt and add attention mask
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
        attention_mask = inputs.attention_mask  # Add the attention mask

        # Generate a response from the model
        outputs = self.model.generate(inputs["input_ids"], attention_mask=attention_mask, max_length=150, do_sample=True, top_k=50, top_p=0.95)

        # Decode the response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    def parse_variables(self, user_input):
        # Basic regex for extracting relevant information, you can improve this over time
        destination_match = re.search(r'\bgoing to ([\w\s]+)', user_input, re.IGNORECASE)
        check_in_match = re.search(r'check in on (\d{4}-\d{2}-\d{2})', user_input)
        check_out_match = re.search(r'check out on (\d{4}-\d{2}-\d{2})', user_input)
        
        if destination_match:
            self.conversation_memory['destination'] = destination_match.group(1)
        if check_in_match:
            self.conversation_memory['check_in_date'] = check_in_match.group(1)
        if check_out_match:
            self.conversation_memory['check_out_date'] = check_out_match.group(1)

    def get_trip_details(self):
        # Prompt the LLM to act as a travel agent and extract user inputs
        agent_prompt = ("You are a travel agent talking to a user planning a trip. "
                        "Start by learning where and when the user is traveling.")
        
        # First interaction (asking about destination and dates)
        response = self.generate_response(agent_prompt)
        print(response)

        # User provides the input
        user_input = input("Your response: ")
        self.parse_variables(user_input)  # Extract destination and dates
        
        # Keep prompting until you gather enough info
        if 'destination' not in self.conversation_memory:
            agent_prompt = "Could you please tell me where you're going?"
            response = self.generate_response(agent_prompt)
            print(response)
            user_input = input("Your response: ")
            self.parse_variables(user_input)

        if 'check_in_date' not in self.conversation_memory:
            agent_prompt = "When would you like to check in?"
            response = self.generate_response(agent_prompt)
            print(response)
            user_input = input("Your response: ")
            self.parse_variables(user_input)

        if 'check_out_date' not in self.conversation_memory:
            agent_prompt = "When would you like to check out?"
            response = self.generate_response(agent_prompt)
            print(response)
            user_input = input("Your response: ")
            self.parse_variables(user_input)
        
        # You can keep expanding with more preferences, etc.
        print("Collected trip details:", self.conversation_memory)

    def display_results(self, hotels, activities):
        # Continue with displaying results as before
        hotel_prompt = f"I found {len(hotels)} hotel options for your trip. Here are the details:\n"
        for hotel in hotels:
            hotel_prompt += f"{hotel['name']} with a price of {hotel['price']} and a rating of {hotel['rating']} stars.\n"
        hotel_response = self.generate_response(hotel_prompt)
        print(hotel_response)

        activity_prompt = f"I found {len(activities)} activities to do in your destination. Here are the options:\n"
        for activity in activities:
            activity_prompt += f"{activity['name']} costs {activity['price']} with a rating of {activity['rating']} stars.\n"
        activity_response = self.generate_response(activity_prompt)
        print(activity_response)

    def run(self):
            trip_details = self.get_trip_details()
            
            # Mock data - replace with API calls later
            hotels = [
                {"name": "Hotel 1", "price": "$150/night", "rating": 4.5},
                {"name": "Hotel 2", "price": "$120/night", "rating": 4.0},
                {"name": "Hotel 3", "price": "$100/night", "rating": 3.8},
            ]
            
            activities = [
                {"name": "City Tour", "price": "$50/person", "rating": 4.7},
                {"name": "Museum Visit", "price": "$20/person", "rating": 4.3},
                {"name": "Hiking Adventure", "price": "$75/person", "rating": 4.9},
            ]
            
            # Display results
            self.display_results(hotels, activities)

# Main function to run the communication agent
def main():
    # Initialize the communication agent with a specific model
    agent = CommunicationAgent(model_name="EleutherAI/gpt-neo-125M")
    
    # Start the trip planning interaction
    agent.run()

if __name__ == "__main__":
    main()