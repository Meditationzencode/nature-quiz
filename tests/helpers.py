def start_quiz(client, difficulty="Easy", category="All"):
    client.post("/start", data={"difficulty": difficulty})
    client.post("/category", data={"category": category})
