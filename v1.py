import requests
import json
from transformers import pipeline
from datetime import datetime
import re
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# import time
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from the .env file

# Replace with your actual Google Maps API key
API_KEY = os.getenv("API_KEY")
testing = 1 #so that I don't have to type inputs everytime
# Initialize the Hugging Face summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# opentable URL

# def search_opentable(restaurant_name, location):
#     search_url = f"https://www.opentable.com/s/?term={restaurant_name}&metroId=72&regionIds=67&dateTime=2024-10-13T19%3A00%3A00&covers=2"
#     print(search_url)
#     try:
#         response = requests.get(search_url, timeout=120)  # Increase the timeout to 120 seconds
#         print(response)
#         if response.status_code == 200:
#             print(f"Search URL: {search_url}")
#             return search_url
#         else:
#             return f"Error: {response.status_code} while fetching OpenTable search results."
#     except requests.exceptions.Timeout:
#         return "Error: The request timed out."
#     except requests.exceptions.RequestException as e:
#         return f"Error: {e}"

def get_user_input():
    if testing == 1:
        location = "fishtown philadelphia"
        group_size = "13"
        date = "2024-10-13"
        time = "18:00-20:00"
        vibe = "fun vibes with cocktails"
        price_range = "2"
        cuisine = ""
    else:
        location = input("Enter the location: ")
        group_size = input("Enter the number of people: ")
        date = input("Enter the date (YYYY-MM-DD): ")
        time = input("Enter the time range (e.g., 18:00-20:00): ")
        vibe = input("Describe the vibe in 1-2 sentences: ")
        price_range = input("Enter price range (optional, 1 is cheapest, 4 is most expensive): ")
        cuisine = input("Enter preferred cuisine (optional): ")
    return {
        "location": location,
        "group_size": group_size,
        "date": date,
        "time": time,
        "vibe": vibe,
        "price_range": price_range,
        "cuisine": cuisine
    }
def is_group(review_text, group_size):
    review_texts = [review['text'] for review in review_text if 'text' in review]
    if not review_texts:
        print("No valid review texts found")
        return 0  # No valid reviews
    combined_reviews = " ".join(review_texts)
    # debugging
    # print(f"Combined review text for classification: {combined_reviews[:500]}...")  # Printing the first 500 characters


    # Define chunk size (character length to approximate token size)
    chunk_size = 1000  # Approximate size to ensure it fits within the model's token limit
    
    # Split the reviews into smaller chunks
    chunks = [combined_reviews[i:i+chunk_size] for i in range(0, len(combined_reviews), chunk_size)]
    
    positive_scores = 0
    total_chunks = len(chunks)
    # print(f"Total chunks created: {total_chunks}")  # DEBUG: Log the number of chunks


    # Classify each chunk and accumulate results
    for chunk in chunks:
        prompt = f"Is this restaurant good for a group of around {group_size} people? {chunk}"
        try:
            result = classifier(prompt)
            label = result[0]['label']
            score = result[0]['score']

            if label == 'POSITIVE':
                positive_scores += score
        except Exception as e:
            print(f"Error during classification: {e}")
            continue  # Skip this chunk if there's an issue
        # result = classifier(prompt)
        # label = result[0]['label']
        
        # # Add to score if classified as 'POSITIVE'
        # if label == 'POSITIVE':
        #     positive_scores += 1
    # print(f"Positive chunks: {positive_scores} out of {total_chunks}")
    avg_score = positive_scores / total_chunks if total_chunks > 0 else 0
    is_group_friendly = positive_scores > 0
    # Return 1 if more than half the chunks are positive, otherwise 0
    return avg_score, is_group_friendly

    # prompt = f"Is this restaurant good for a group of people? {review_text}"
    
    # # Classify the text to determine group suitability
    # result = classifier(prompt)
    
    # # Extract the probability (score)
    # label = result[0]['label']  # e.g., 'POSITIVE' or 'NEGATIVE'
    # score = result[0]['score']  # Probability score (e.g., 0.95)
    # if label == 'POSITIVE':
    #     return 1
    # else:
    #     return 0
    
    # return label, score

def get_place_details(place_id):
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}"
    response = requests.get(details_url)
    if response.status_code == 200:
        return response.json().get("result", {})
    else:
        print("Error fetching place details")
        return {}

# get restaurant list from google maps, check restaurants for group friendliness, return top 3 resaurants
def search_restaurants(location, cuisine, price_range, group_size):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={cuisine}+restaurants+in+{location}&key={API_KEY}"
    
    if price_range:
        url += f"&minprice={price_range}&maxprice={price_range}"
    
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get("results", [])
        # print("Raw results:", json.dumps(results, indent=2))  # Check raw data from Google Maps API
        ranked_restaurants = []
        min_rating = 4.5
        filtered_results = [restaurant for restaurant in results if restaurant.get('rating', 0) >= min_rating]
        # Check group-friendliness for each restaurant
        for restaurant in filtered_results:
            place_id = restaurant['place_id']
            place_details = get_place_details(place_id)
            # print(json.dumps(place_details, indent=2))
            reviews = place_details.get('reviews',[])
            reservation_url = place_details.get("reserve_url")
            if reservation_url:
                print(reservation_url)
            # name = place_details.get('name')
            # if name == 'New Orleans Creole Cookery':
            #     print('this is KNOWN RESTARAAUNT')
            if not reviews:
                print(f"No reviews found for {restaurant.get('name')}")
                continue  # Skip if no reviews are available
            # review_texts = [review['text'] for review in reviews if 'text' in review]
            avg_score, is_group_friendly = is_group(reviews, group_size)
            if is_group_friendly:
                ranked_restaurants.append((place_details,avg_score))
                # if name == 'New Orleans Creole Cookery':
                #     print('this is KNOWN RESTARAAUNT')
                # print("added to rank")
            # Count group-friendly reviews
            # group_friendly_reviews = [review for review in place_details.get('reviews',[]) if is_group(review['text'])]
            # group_friendly_reviews = [review for review in place_details.get('reviews', []) if find_group_mentions(review['text'], group_size)]
            # group_score = len(group_friendly_reviews)  # Ranking based on number of group-friendly reviews
            
            # ranked_restaurants.append((restaurant, group_score))
        
        # Sort restaurants by group score (highest first) and take top 3
        ranked_restaurants.sort(key=lambda x: x[1], reverse=True)
        top_restaurants = [restaurant for restaurant, _ in ranked_restaurants[:10]]
        # top_3_restaurants = ranked_restaurants[:3]
        # print(top_3_restaurants)
        # top_restaurants = []
        # for restaurant in results[:3]:
        #     place_id = restaurant['place_id']
        #     place_details = get_place_details(place_id)
        #     top_restaurants.append(place_details)
        return top_restaurants
        # return response.json().get("results", [])[:3]  # return top 3 results
    else:
        print("Error fetching restaurant data")
        return []

def summarize_reviews(reviews):
    # Step 1: Extract review texts
    review_texts = [review['text'] for review in reviews if 'text' in review]
    
    # Check if there are any reviews
    if not review_texts:
        return "No reviews available."

    # Step 2: Summarize the reviews using a Hugging Face model
    combined_reviews = " ".join(review_texts)  # Combine all reviews into a single text
    if len(combined_reviews) > 1024:  # Ensure input size is reasonable for summarization
        combined_reviews = combined_reviews[:1024]
    
    summary = summarizer(combined_reviews, max_length=100, min_length=30, do_sample=False)[0]['summary_text']

    # Step 3: Get the relative time of the last review
    last_review_time = max([review['relative_time_description'] for review in reviews])
    
    # Step 4: Return the summary and last review recency
    review_summary = f"Summary: {summary}\n\nLast review: {last_review_time}"
    return review_summary

def generate_booking_link(restaurant, date, time, people):
    # opentable_url = f"https://www.opentable.com/s/?datetime={date}T{time}&covers={people}&restaurant={restaurant['name']}"
    name = restaurant.get('name')
    search_url = f"https://www.opentable.com/s/?term={name}&metroId=72&regionIds=67&dateTime=2024-10-13T19%3A00%3A00&covers=2"
    # opentable_url = f"https://www.opentable.com/r/{restaurant['name'].replace(' ', '-').lower()}?p={people}&sd={date}T{time}:00"
    return search_url

# format the results once given top 3 restaurant list
def display_results(restaurants, user_input):
    print("\nTop 10 restaurant recommendations:\n")
    for restaurant in restaurants:
        name = restaurant.get("name")
        address = restaurant.get("formatted_address")
        reviews = restaurant.get("reviews", [])
        # reviews = restaurant.get("user_ratings_total", 0)
        review_summary = summarize_reviews(reviews)
        # summary = summarize_reviews(restaurant.get("reviews", []))
        reservation_url = restaurant.get("reserve_url")
        if not reservation_url:
            # Check if Google has a "third-party attribution" section with a reservation link
            for attribution in restaurant.get('attributions', []):
                if 'reserve' in attribution.get('html_attribution', ''):
                    reservation_url = attribution['html_attribution']
                else:
                    reservation_url = "No reservation URL found"
        print(f"Name: {name}")
        print(f"Address: {address}")
        # print(f"Total Reviews: {reviews}")
        print(f"Review Summary: {review_summary}")
        # print(f"Reservation URL:{reservation_url}")
        # booking_link = generate_booking_link(restaurant, user_input['date'], user_input['time'].split('-')[0], user_input['group_size'])
        # print(f"Booking Link (OpenTable): {booking_link}")
        print("-" * 50)

def main():
    user_input = get_user_input()
    restaurants = search_restaurants(user_input["location"], user_input["cuisine"], user_input["price_range"], user_input["group_size"])
    
    if restaurants:
        display_results(restaurants, user_input)
    else:
        print("No restaurants found matching the criteria.")

if __name__ == "__main__":
    main()
