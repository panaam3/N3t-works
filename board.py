import tkinter as tk
import copy

BOARD_SIZE = 8
SQUARE_SIZE = 50
MAX_NUM_PLY = 100

# Note: black is always at top of board + always uses uppercase letters in underlying board

class RawChessBoard:
	def __init__(self, board=None, number_of_total_moves=None, game_status=None):
		if board is None and board is None and game_status is None:
			self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
			self.number_of_total_moves = 0
			self.game_status = None # win(-1)/draw(0)
		else:
			self.board = board
			self.number_of_total_moves = 0
			self.game_status = game_status

	def is_position_empty(self, new_row, new_col):
		piece = self.board[new_row][new_col]
		return piece is None

	def is_capture(self, src_row, src_col, dest_row, dest_col):
		old_position = self.board[src_row][src_col]
		dest_position = self.board[dest_row][dest_col]
		if dest_position is None: #there is no item in new position
			return False
		if old_position.islower() != dest_position.islower(): #if there is a piece, check if there is a different colored piece
			return True
		return False

	def gives_check(self, src_row, src_col, dest_row, dest_col, color_of_opponent):
		old_position = self.board[src_row][src_col]
		dest_position = self.board[dest_row][dest_col]
		if dest_position is None: #there is no item in new position
			return False

		king_x, king_y = self.find_king(color_of_opponent)
		if not king_x and not king_y: #if there is no king on board
			return False

		if dest_row == king_x and dest_col == king_y: #if the piece can move to the king's position then thats a capture
			return True

		return False

	def is_forward_move(self, src_row, src_col, dest_row, dest_col, color_of_opponent):
		if color_of_opponent == 'black':
			return src_row < dest_row
		elif color_of_opponent == 'white':
			return src_row < dest_row
		return False

	def find_king(self, color):
		for r in range(BOARD_SIZE):
			for c in range(BOARD_SIZE):
				p = self.board[r][c]
				if p and p.lower() == 'k': #finding any king
					symbol = 'K' if color == 'black' else 'k'
					if p == symbol:
						return r, c
		return None, None

	def find_king_in_checkmate(self): #will return color that lost
		colors = ['white', 'black']
		for color in colors:
			row, col = self.find_king(color)
			
			if self.is_king_in_checkmate(color):
				return color
		return None

	def is_check(self, color):
		row, col = self.find_king(color)

		if not row and not col:
			return False
		
		opponent_color = 'black' if color == 'white' else 'white'

		possible_moves = self.get_playable_moves(opponent_color)
		for move_record in possible_moves:
			for possible_dest in move_record['moves']:
				dest_row, dest_col = possible_dest[0], possible_dest[1]
				if row == dest_row and dest_col == col:
					return True

		return False
		
	def is_king_in_checkmate(self, color):
		if not self.is_check(color):
			return False

		#check if every possible move still means we are in check
		possible_moves = self.get_playable_moves(color)
		for move_record in possible_moves:
			src_row, src_col = move_record['row'], move_record['col']
			for possible_dest in move_record['moves']:
				dest_row, dest_col = possible_dest[0], possible_dest[1]

				temp_board = RawChessBoard(self.board, self.number_of_total_moves, self.game_status)
				temp_board.move_piece(color, src_row, src_col, dest_row, dest_col)
				if not temp_board.is_check(color):
					return False
				del temp_board

		return True


	def increase_number_of_moves(self, move_count=1):
		self.number_of_total_moves += move_count

	def is_terminal(self, color):
		possible_moves = self.get_playable_moves(color)

		if len(possible_moves) == 0:
			return True

		if self.number_of_total_moves >= MAX_NUM_PLY:
			return True
		return False

	def get_state_after_move(self, color, curr_x, curr_y, next_x, next_y): #assumes next position is possible. no logic to check consistency
		new_board = list(self.board)
		new_board[next_x][next_y] = self.board[curr_x][curr_y]
		new_board[curr_x][curr_y] = None
		return new_board

	def get_rook_moves(self, start_row, start_col):
		moves = []
		piece = self.board[start_row][start_col]
		
		directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
		
		for dr, dc in directions:
			for i in range(1, 8):
				nr, nc = start_row + dr * i, start_col + dc * i
				
				if 0 <= nr < len(self.board) and 0 <= nc < len(self.board[0]):
					target = self.board[nr][nc]
				
					if target is None:
						moves.append((nr, nc))
					else:
						if target.islower() != piece.islower():
							moves.append((nr, nc))
						break
				else:
					break
					
		return moves

	def get_knight_moves(self, start_row, start_col):
		moves = []
		
		potential_offsets = [
			(-2, -1), (-2, 1), 
			(-1, -2), (-1, 2),
			(1, -2), (1, 2), 
			(2, -1), (2, 1)
		]

		for dr, dc in potential_offsets:
			end_row, end_col = start_row + dr, start_col + dc

			if 0 <= end_row < BOARD_SIZE and 0 <= end_col < BOARD_SIZE:
				target_piece = self.board[end_row][end_col]
				if target_piece is None or target_piece.islower() != self.board[start_row][start_col].islower():
					moves.append((end_row, end_col))
		return moves

	def get_queen_moves(self, start_row, start_col):
		moves = []
		
		directions = [
			(-1, 0), (1, 0), (0, -1), (0, 1),  # Rook-like
			(-1, -1), (-1, 1), (1, -1), (1, 1) # Bishop-like
		]

		for dr, dc in directions:
			for i in range(1, BOARD_SIZE):
				end_row = start_row + dr * i
				end_col = start_col + dc * i

				if 0 <= end_row < BOARD_SIZE and 0 <= end_col < BOARD_SIZE:
					target_piece = self.board[end_row][end_col]
					
					if target_piece is None:
						moves.append((end_row, end_col))
					elif target_piece.islower() != self.board[start_row][start_col].islower():
						moves.append((end_row, end_col))
						break
					else:
						break
				else:
					break
		
		return moves

	def get_king_moves(self, start_row, start_col):
		moves = []
		
		directions = [
			(-1, -1), (-1, 0), (-1, 1), # Top
			(0, -1),		   (0, 1), # Middle
			(1, -1),  (1, 0),  (1, 1) # Bottom
		]

		for dr, dc in directions:
			end_row, end_col = start_row + dr, start_col + dc

			if 0 <= end_row < BOARD_SIZE and 0 <= end_col < BOARD_SIZE:
				target_piece = self.board[end_row][end_col]
				
				if target_piece is None or target_piece.islower()!= self.board[start_row][start_col].islower():
					moves.append((end_row, end_col))
		
		return moves

	def get_bishop_moves(self, start_row, start_col):
		moves = []
		piece = self.board[start_row][start_col]
		
		directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
		
		for dr, dc in directions:
			for i in range(1, 8):
				nr, nc = start_row + dr * i, start_col + dc * i
				
				if 0 <= nr < len(self.board) and 0 <= nc < len(self.board[0]):
					target = self.board[nr][nc]
					
					if target is None:
						moves.append((nr, nc))
					else:
						if target.islower() != piece.islower():
							moves.append((nr, nc))
						break
				else:
					break
		return moves

	def get_pawn_moves(self, row, col): #TODO? En passant
		moves = []
		piece = self.board[row][col]
		
		direction = -1 if piece.islower() else 1
		start_row = 6 if piece.islower() else 1
		
		#Forward move
		nr, nc = row + direction, col
		if 0 <= nr < BOARD_SIZE:
			if self.board[nr][nc] is None:
				moves.append((nr, nc))
				
				#possible initial double move
				if row == start_row:
					nr2, nc2 = row + (2 * direction), col
					if self.board[nr2][nc2] is None:
						moves.append((nr2, nc2))

		#pawn apture
		for dc in [-1, 1]:
			nr, nc = row + direction, col + dc
			if 0 <= nr < len(self.board) and 0 <= nc < len(self.board[0]):
				target = self.board[nr][nc]
				if target is not None and self.is_pos_same_color(target, piece):
					moves.append((nr, nc))
					
		return moves

	def is_pos_same_color(self, value1, value2):
		return (value1.islower() and value2.islower()) or (value1.isupper() and value2.isupper())

	def get_playable_moves(self, color):
		played_moves = []

		for row in range(BOARD_SIZE):
			for col in range(BOARD_SIZE):
				if self.board[row][col]:
					curr_piece_color = 'white' if self.board[row][col].islower() else 'black'
					if color == curr_piece_color:
						match self.board[row][col].lower():
							case 'p':
								moves = self.get_pawn_moves(row, col)
								rslt = {'piece':'P' if color == 'black' else 'p', 'color':color, 'moves': moves, 'row':row, 'col':col}
								played_moves.append(rslt)
							case 'r':
								moves = self.get_rook_moves(row, col)
								rslt = {'piece':'R' if color == 'black' else 'r', 'color':color, 'moves': moves, 'row':row, 'col':col}
								played_moves.append(rslt)
							case 'b':
								moves = self.get_bishop_moves(row, col)
								rslt = {'piece':'B' if color == 'black' else 'b', 'color':color, 'moves': moves, 'row':row, 'col':col}
								played_moves.append(rslt)
							case 'n':
								moves = self.get_knight_moves(row, col)
								rslt = {'piece':'N' if color == 'black' else 'n', 'color':color, 'moves': moves, 'row':row, 'col':col}
								played_moves.append(rslt)
							case 'k':
								moves = self.get_king_moves(row, col)
								rslt = {'piece':'K' if color == 'black' else 'k', 'color':color, 'moves': moves, 'row':row, 'col':col}
								played_moves.append(rslt)
							case 'q':
								moves = self.get_queen_moves(row, col)
								rslt = {'piece':'Q' if color == 'black' else 'q', 'color':color, 'moves': moves, 'row':row, 'col':col}
								played_moves.append(rslt)
		return played_moves

	def __getitem__(self, loc):
		return self.board[loc]

	def move_piece(self, color, curr_x, curr_y, next_x, next_y): #assumes next position is possible. not logic to check consistency
		self.board = self.get_state_after_move(color, curr_x, curr_y, next_x, next_y)
		self.increase_number_of_moves()

class ChessBoardGUI:
	def __init__(self, master, underlying_board):
		self.master = master
		self.canvas = tk.Canvas(master, width=SQUARE_SIZE * BOARD_SIZE, height=SQUARE_SIZE * BOARD_SIZE)
		self.uboard = underlying_board
		self.canvas.pack()

		self.images = {'black-k' : tk.PhotoImage(file="./assets/bk.png"),
						'black-r': tk.PhotoImage(file="./assets/br.png"),
						'black-n': tk.PhotoImage(file="./assets/bn.png"),
						'black-b': tk.PhotoImage(file="./assets/bb.png"),
						'black-q': tk.PhotoImage(file="./assets/bq.png"),
						'black-p': tk.PhotoImage(file="./assets/bp.png"),
						'white-p': tk.PhotoImage(file="./assets/wp.png"),
						'white-k': tk.PhotoImage(file="./assets/wk.png"),
						'white-r': tk.PhotoImage(file="./assets/wr.png"),
						'white-n': tk.PhotoImage(file="./assets/wn.png"),
						'white-b': tk.PhotoImage(file="./assets/wb.png"),
						'white-q': tk.PhotoImage(file="./assets/wq.png")
						}
		self.existing_imgs_by_ids = []

		#scale images
		for k,v in self.images.items():
			self.images[k] = v.subsample(20, 20)
		
		for row in range(BOARD_SIZE):
			for col in range(BOARD_SIZE):
				x1, y1 = col * SQUARE_SIZE, row * SQUARE_SIZE
				x2, y2 = (col + 1) * SQUARE_SIZE, (row + 1) * SQUARE_SIZE
				color = "white" if (row + col) % 2 == 0 else "black"
				self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)
		
		self.place_pieces()

	def move_piece(self, color, curr_x, curr_y, next_x, next_y): #assumes next position is possible. not logic to check consistency
		self.uboard.move_piece(color, curr_x, curr_y, next_x, next_y)
		self.place_pieces(False)

	#draw pieces
	def place_pieces(self, is_init=True):
		for img_id in self.existing_imgs_by_ids: #remove old positions, if there any
			self.canvas.delete(img_id)

		if is_init:
			piece_types = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
			for i in range(BOARD_SIZE):
				self.uboard[0][i] = piece_types[i]
				self.uboard[BOARD_SIZE-1][i] = piece_types[i].lower()

			for i in range(BOARD_SIZE):
				self.uboard[1][i] = 'P'
				self.uboard[6][i] = 'p'

		for row in range(BOARD_SIZE):
			for col in range(BOARD_SIZE):
				if self.uboard[row][col]:
					x, y = col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2
					text_color = "black" if (row + col) % 2 == 0 else "white"
					square_color = "white" if (row + col) % 2 == 0 else "black"
					piece_color = 'white' if self.uboard[row][col].islower() else 'black'

					#self.canvas.create_text(x,y, text=self.board[row][col], fill=text_color)

					piece_name = '{0}-{1}'.format(piece_color, self.uboard[row][col].lower())
					img_id = self.canvas.create_image(x, y, image= self.images[piece_name]) #creating new image position
					self.existing_imgs_by_ids.append(img_id)
					self.canvas.tag_raise(img_id)