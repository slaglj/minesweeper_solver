"""
The code to track the internals of a game of minesweeper in the form of
a MinesweeperGame object. There is no code pertaining to the display of
the game or any sort of user interface - see the display module for that.


classes
	MinesweeperGame - data structure representing a minesweeper game
"""

# Jacob C. Slagle, 2018

from exceptions import *

import itertools
import collections 

class MinesweeperGame:
	"""
	A MinesweeperGame object tracks the state of a game of Minesweeper

	A MinesweeperGame is a data structure that manages all of the 
	internals of a minesweeper game, but does not manage any interface with a
	player. Another class must use a MinesweeperGame object and act as an
	interface with a player to run a "full" game.

	Methods

		Move Methods
			place_flag() - place flag on board
			remove_flag() - remove flag from board
			toggle_flag() - switch between flag or unflagged
			reveal() - reveal square

		Query Methods
			is_flagged() - check if square is flagged
			is_revealed() - check if square is revealed
			num_mines_surrounding() - get number of mines around square
			contains_mine() - check if sqaure contains mine

		Iterator Methods:
			board_iterator() - return iterator over game board
			neighbors() - return iterator over a square's neighbors
			flagged_neighbors() - return iterator over a square's flagged neighbors
			revealed_neighbors() - return iterator over a square's revealed neighbors
			blank_neighbors() - return iterator over a square's revealed neighbors
			random_point()

		Miscellaneous:
			add_move_protocol()

	"""
	#------------------------------------------------------------------------#
	# The following methods implement the moves a player can make, i.e.      #
	# things they can do to change the state of the game.                    #
	#------------------------------------------------------------------------#

	def place_flag(self, point):
		"""Place flag at point

		Do nothing if there already is a flag at point

		Args:
			point (tuple of ints) -- coordinate point on the game board

		Raises:
			GameOverException -- raised if the game is already over
		"""
		if self.is_over:
			raise GameOverException

		if self.is_revealed(point):
			# Don't allow player to flag revealed squares
			return

		square = self._get_square(point)
		if not square.is_flagged:
			square.is_flagged = True

			for prot in self.move_protocols:
				prot(point,'flag')

	def remove_flag(self, point):
		"""Remove flag from point

		Does nothing if there was no flag at point

		Args:
			point (tuple of ints) -- coordinate point on the game board

		Raises:
			GameOverException -- raised if the game is already over
		"""
		if self.is_over:
			raise GameOverException
		square = self._get_square(point)
		if square.is_flagged:
			square.is_flagged = False

			for prot in self.move_protocols:
				prot(point,'unflag')

	def toggle_flag(self, point):
		"""Change point from unflagged to flagged, or vice versa

		Args:
			point (tuple of ints) -- coordinate point on the game board

		Raises:
			GameOverException -- raised if the game is already over
		"""
		if self.is_flagged(point):
			self.remove_flag(point)
		else:
			self.place_flag(point)

	def reveal(self, point):
		"""Reveal the square at the given point

		Args:
			point (tuple of ints) -- coordinate point on the game board

		Raises:
			GameOverException -- raised if the game is already over
		"""
		if self.is_over:
			raise GameOverException

		if self.is_flagged(point):
			# Don't allow player to reveal flagged mines
			return 

		if not self.mines_placed:
			self._place_mines(first_move = point)
			self.mines_placed = True

		if self.is_revealed(point):
			return

		square = self._get_square(point)
		square.is_revealed = True

		for prot in self.move_protocols:
				prot(point,'reveal')
 

		self.num_revealed += 1

		if square.contains_mine:
			# End the game.
			self.is_over = True
			raise GameLostException

		if self.num_revealed == self.num_free:
			self.is_over = True
			raise GameWonException

		if square.num_surrounding == 0:
			# Save player time revealing squares in adjacent squares when none
			# of them contain mines.
			for neighb in self.neighbors(point):
				self.reveal(neighb)
			return

	#------------------------------------------------------------------------#
	# The following methods are used to acquire certain information about a  #
	# given point on the game board.                                         #
	#------------------------------------------------------------------------#

	def is_flagged(self,point):
		"""Return true if point is flagged
		
		Args:
			point (tuple of ints) -- coordinate point on the game board

		Returns:
			bool -- indicates presence of flag

		"""
		square = self._get_square(point)
		return square.is_flagged

	def is_revealed(self,point):
		"""Return true if point is revealed
		
		Args:
			point (tuple of ints) -- coordinate point on the game board

		Returns:
			bool -- indicates square is revealed

		"""
		return self._get_square(point).is_revealed

	def num_mines_surrounding(self, point):
		"""Return number of mines surrounding point
		
		Args:
			point (tuple of ints) -- coordinate point on the game board

		Return:
			If the square at point is revealed or the game is over, return
			the number of mines in adjacent squares. Otherwise, (if the square
			is revealed or the game is not over) return None.
		"""
		if self.is_over or self.is_revealed(point):
			return self._get_square(point).num_surrounding
		else:
			raise GameNotOverException("Can not access number of surrounding mines of unrevealed square before the game is over.")

	def contains_mine(self,point):
		"""If game is over, indicates if there is a mine at point.
		
		Args:
			point (tuple of ints) -- coordinate point on the game board

		Return:
			bool indicating if there is a mine at point

		Raises:
			GameNotOverException if the game isn't over
		"""
		if self.is_over:
			return self._get_square(point).contains_mine
		else:
			raise GameNotOverException("Can not show if a square contains a mine before the game is over")

	#------------------------------------------------------------------------#
	# The following methods return iterators over certain subsets of the     #
	# board, the exception being random_point which returns just one point.  #
	#------------------------------------------------------------------------#
	
	def board_iterator(self):
		"""Return an iterator going over all points on the game board"""
		return itertools.product(*[range(self.dimensions[dim]) for dim in range(len(self.dimensions))])

	def neighbors(self, point):
		"""Return iterator over coordinate points adjacent (or diagonally adjacent) to a point on game board

		point -- a tuple representing a point on the board
		
		Include all points directly and diagonally adjacent, exclude point itself.
		"""

		# coordinate_ranges will include the range of values included in each dimension
		# e.g. coordinate_ranges[0] will give the range of x-values to be included.
		coordinate_ranges = [] 
		for dim in range(len(self.dimensions)):
			# make sure ranges lie within game board
			coordinate_range = range(max(0,point[dim] - 1), min(point[dim] + 2, self.dimensions[dim]))
			coordinate_ranges.append(coordinate_range)

		# Take the cartesian product of the coordinate ranges, put it in a list.
		is_not_point = lambda x: x != point
		return filter(is_not_point,itertools.product(*coordinate_ranges))

	def flagged_neighbors(self,point):
		return filter(self.is_flagged,self.neighbors(point))

	def revealed_neighbors(self,point):
		return filter(self.is_revealed,self.neighbors(point))

	def blank_neighbors(self,point):
		is_blank = lambda x: not self.is_flagged(x) and not self.is_revealed(x)
		return filter(is_blank,self.neighbors(point))

	def random_point(self):
		"""Return a random point on the board"""
		from random import randint
		return tuple([randint(0, self.dimensions[dim] - 1) for dim in range(len(self.dimensions))])

	#------------------------------------------------------------------------#
	# Method to facilitate "watching" game progress                          #
	#------------------------------------------------------------------------#

	def add_move_protocol(self,prot):
		"""Adds a protocol to execute in response to gameplay

			Whenever a move is made at a point, the protocol is "notified" of 
			which point was affected and by what kind of move ('reveal','flag',
			'unflag'), and the protocol is executed. What the protocol can do
			is arbitrary, although it should do minimal work.
			
			Args:
				prot (function) -- a function of the form prot(point,move_type)
					where point is a point on the game board and move_type is 
					a string in the set {'reveal','flag','unflag'}. 
		"""
		self.move_protocols.append(prot)

	#------------------------------------------------------------------------#
	# Non-public methods                                                     #
	#------------------------------------------------------------------------#

	def __init__(self, dimensions = (8,8), mines = None, num_mines = -1):
		# dimensions is a tuple of board dimensions, 
		# usually of length two, i.e. (length, width). However, we allow the
		# possiblity of 3-dimensional or n-dimensional games of minesweeper
		self.dimensions = dimensions
		from operator import mul
		from functools import reduce
		num_squares = reduce(mul,self.dimensions)

		# grid is the game board, initially just an array of Squares, each
		# of which has default values for members
		self.grid = self._build_grid(0)

		self.mines = mines

		if self.mines:
			self.mines = set(mines)
			self.num_mines = len(mines)
			self._place_mines()
			self.mines_placed = True
		else:
			self.num_mines = num_mines
			self.mines_placed = False

		if self.num_mines < 0:
			self.num_mines = int(num_squares/5)
		self.num_free = num_squares - self.num_mines

		self.is_over = False
		self.num_revealed = 0

		self.move_protocols = []

		

	def _build_grid(self, dim):
		# Build a game board, i.e. an n-dimensional array of Squares
		# where n == len(self.dimensions) and the dimensions are given 
		# by self.dimensions
		#
		# Squares are created with default values, to be updated by 
		# _place_mines
		if dim == len(self.dimensions):
			return self.Square()
		return [self._build_grid(dim+1) for _ in range(self.dimensions[dim])]

	# A Square is an object representing one square in a minesweeper grid.  It
	# simply packages all data relevant to one coordinate in a single object.
	class Square:
		def __init__(self, contains_mine = False, num_surrounding = -1, 
					is_revealed = False, is_flagged = False):
			self.contains_mine = contains_mine
			self.num_surrounding = num_surrounding  # number of mines in adjacent squares
			self.is_revealed = is_revealed
			self.is_flagged = is_flagged

	def _get_square(self, point):
		cross_section = self.grid

		for dim in range(len(self.dimensions)):
			cross_section = cross_section[point[dim]]

		return cross_section

	def _place_mines(self,first_move = None):
		if not self.mines:
			
			# freebies are the spaces adjacent to first_move where no mines should be placed
			# i.e. "freebie" spaces given to the player
			freebies = set([])
			if first_move:
				freebies = set(self.neighbors(first_move))
				freebies.add(first_move)

			self.mines = set([])
			while len(self.mines) < self.num_mines:
				rpoint = self.random_point()

				if rpoint not in freebies:
					self.mines.add(rpoint)

		for mine in self.mines:
			square = self._get_square(mine)
			square.contains_mine = True


		# update num_surrounding field for each Square in the board
		for point in self.board_iterator():
			square = self._get_square(point)

			adj_squares = [self._get_square(neighb) for neighb in self.neighbors(point)]

			square.num_surrounding = [adj_square.contains_mine for adj_square in adj_squares].count(True)






		


