import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.routing import WebSocketRoute
from starlette.templating import Jinja2Templates

app = FastAPI()

# Mount the "static" directory to serve static files (CSS, JavaScript, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates for rendering HTML
templates = Jinja2Templates(directory="templates")

class Game:
    """
    Class representing the Memory Card Game.
    """
    def __init__(self, rows: int, cols: int):
        """
        Initialize the game with the specified number of rows and columns.
        """
        self.rows = rows
        self.cols = cols
        self.flipped = []
        self.board = self.initialize_board()

    def initialize_board(self):
        """
        Initialize the game board with shuffled pairs of symbols.
        """
        symbols = ["A", "B", "C", "D", "E", "F", "G", "H"]
        num_pairs = (self.rows * self.cols) // 2
        pairs = random.sample(symbols, num_pairs) * 2
        random.shuffle(pairs)

        board = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        for row in range(self.rows):
            for col in range(self.cols):
                board[row][col] = pairs.pop()

        return board

    def flip_card(self, row: int, col: int):
        """
        Flip a card at the specified row and column.
        """
        if (row, col) not in self.flipped and len(self.flipped) < 2:
            self.flipped.append((row, col))

    def check_match(self):
        """
        Check if the flipped cards form a matching pair.
        """
        if len(self.flipped) == 2:
            card1 = self.board[self.flipped[0][0]][self.flipped[0][1]]
            card2 = self.board[self.flipped[1][0]][self.flipped[1][1]]
            return card1 == card2
        return False

    def reset_flipped(self):
        """
        Reset the list of flipped cards.
        """
        self.flipped = []

# Create a Game instance with 4 rows and 4 columns
game = Game(rows=4, cols=4)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for handling game communication with clients.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            row, col = map(int, data.split(","))
            game.flip_card(row, col)
            if len(game.flipped) == 2:
                match = game.check_match()
                await websocket.send_text(str(match))
                game.reset_flipped()
    except WebSocketDisconnect:
        pass

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Route to render the game interface using Jinja2 template.
    """
    return templates.TemplateResponse("index.html", {"request": None, "rows": game.rows, "cols": game.cols})

@app.websocket_route("/ws-feed")
async def websocket_route():
    """
    WebSocket route for serving the WebSocket communication.
    """
    return WebSocketRoute(websocket_endpoint)
