"""
Transient classes for ease of conversion from discord objects to gpt-readable objects
"""

import discord
import sub.users as memory

class InvalidMediaException(Exception):
    def __init__(self, *args) -> None:
        super().__init__(*args)

class TransientUser:
    def __init__(self, id: int, name: str | None = None, nickname: str | None = None) -> None:
        if name == None:
            name = "unknown"

        self.id = id # discord user ID
        self.name = name # name from memory
        self.nickname: str | None = nickname
        self.role = "user"
        self.special = False # true for users without ids, system/jarvis
    
    def __str__(self) -> str:
        if self.nickname is not None:
            return f"{self.name} (discord nickname:'{self.nickname}') (ID:{self.id})"
        else:
            return f"{self.name} (ID:{self.id})"

    @classmethod
    def from_discord(cls, user: discord.User | discord.Member) -> 'TransientUser':
        if user.id == 1373241417211838474: # jarvis id
            return AssistantUser()
        else:
            memory_recall = memory.get_user(user.id)
            if isinstance(user, discord.Member):
                if memory_recall == None:
                    return TransientUser(user.id, None, user.nick)
                else:
                    try:
                        n = user.nick
                    except AttributeError:
                        n = None
                    return TransientUser(user.id, memory_recall["name"], n)
            else:
                if memory_recall == None:
                    return TransientUser(user.id, None)
                else:
                    return TransientUser(user.id, memory_recall["name"])

class SystemUser(TransientUser):
    def __init__(self):
        super().__init__(-1, "system")
        self.special = True
        self.role = "system"
    
    def __str__(self) -> str:
        return "system"

class AssistantUser(TransientUser):
    def __init__(self):
        super().__init__(-1, "jarvis")
        self.special = True
        self.role = "assistant"
    
    def __str__(self) -> str:
        return "jarvis"

class TransientAttatchment:
    def __init__(self, url: str) -> None:
        self.url = url # this should always be to a valid image
    
    @classmethod
    def from_discord(cls, attatchment: discord.Attachment) -> 'TransientAttatchment':
        image_url_types = [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp"
        ]

        plaintext_copy_types = [
        ]

        print(attatchment.content_type)
        if attatchment.content_type in image_url_types:
            return TransientAttatchment(attatchment.url)
        else:
            raise InvalidMediaException(f"Attatchment '{attatchment.url}' has an invalid media type.")

class TransientMessage:
    def __init__(self, author: TransientUser | None = None, text: str | None = None, attatchments: list[TransientAttatchment] | None = None) -> None:
        if author == None:
            author = TransientUser(-1)
        
        if text == None:
            text = ""
        
        if attatchments == None:
            attatchments = []

        self.author = author
        self.text = text
        self.attachments = attatchments

    @classmethod    
    def from_discord(cls, message: discord.Message) -> 'TransientMessage':
        author = TransientUser.from_discord(message.author)
        attatchments = [
            TransientAttatchment.from_discord(attatchment)
        for attatchment in message.attachments]
        text = message.content

        return TransientMessage(author, text, attatchments)

    def to_gpt(self) -> dict:
        r = {}
        r["role"] = self.author.role
        
        # handle attatchments
        content_list = [
            {
                "type": "image_url",
                "image_url": {"url": attatchment.url}
            }
        for attatchment in self.attachments]

        # add message text
        if not self.author.special:
            self.text = str(self.author) + ": " + self.text # add user name and id before message content
        content_list.append({
            "type": "text",
            "text": self.text
        })

        r["content"] = content_list

        return r