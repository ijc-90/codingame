import sys
import math
import random
from functools import reduce

BIGNUMBER = 999999

def debuggear(message):
    pass
    print(message, file=sys.stderr)

normalPelletList = []
superPelletList = []


# def movePacman(pacId, x, y):
#    print("MOVE " + str(pacId) + " " + str(x) + " " + str(y))


# Grab the pellets as fast as you can!

# width: size of the grid
# height: top left corner is (x=0, y=0)
width, height = [int(i) for i in input().split()]

def winner(loser):
    if loser == 'ROCK':
        return 'PAPER'
    if loser == 'PAPER':
        return 'SCISSORS'
    if loser == 'SCISSORS':
        return 'ROCK'

def winsAgainst(first,second):
    if first == 'ROCK' and second =='SCISSORS':
        return True
    if first =='SCISSORS' and second == 'PAPER':
        return True
    if first =='PAPER' and second == 'ROCK':
        return True
    return False

def randomPoint():
    tries = 0
    while True:
        tries = tries +1
        point = Point(random.randrange(width - 1), random.randrange(height - 1))
        #debuggear(pointsOnMap)
        if reachablePoint(point) and not pointsOnMap[point.x][point.y]:
            return point
        if tries > 5:
            for i in range(len(pointsOnMap)):
                for j in range(len(pointsOnMap[i])):
                    if not pointsOnMap[i][j]:
                        return Point(i,j)



def validPoint(point):
    return point.x < width and point.x >= 0 and point.y <= height and point.y >= 0

pointsOnMap = []
rows = []
for i in range(width):
    pointsOnMap.append([])

for i in range(height):
    row = input()  # one line of the grid: space " " is floor, pound "#" is wall
    for j in range(len(row)):
        if row[j] == "#":
            pointsOnMap[j].append(True) #Already visited or unreachable 
        if row[j] == " ":
            pointsOnMap[j].append(False) #Reachable and unvisited
    rows.append(row)



def reachablePoint(point):
    if not validPoint(point):
        return False
    return rows[point.y][point.x] == " "


def adjacentReachablePoints(point):
    if not reachablePoint(point):
        return []
    x = point.x
    y = point.y
    up = Point(x, (y - 1) % height)
    down = Point(x, (y + 1) % height)
    left = Point((x - 1) % width, y)
    right = Point((x + 1) % width, y)
    return list(filter(reachablePoint, [up, down, left, right]))

class GameState:
    def __init__(self):
        self.recalculateSuperPelletObjectives = True
    
    def getRecalculateSuperPelletObjectives(self):
        return self.recalculateSuperPelletObjectives
    
    def setRecalculateSuperPelletObjectives(self, value):
        self.recalculateSuperPelletObjectives = value


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def asString(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"
    
    def connected(self, otherPoint):
        return self.naiveDistance(otherPoint) == 1 and self.distance(otherPoint) == 1

    def naiveDistance(self, otherPoint):
        return abs(self.x - otherPoint.x) + abs(self.y - otherPoint.y)

    def distance(self, otherPoint):
        return self.realDistance(otherPoint, 10)
    
    def detailedDistance(self, otherPoint):
        return self.realDistance(otherPoint, 28)

    def isEqual(self, other):
        return other is not None and self.x == other.x and self.y == other.y

    def realDistance(self, otherPoint, limit):
        if not reachablePoint(self) or not reachablePoint(otherPoint):
            # debuggear("not reachable")
            return BIGNUMBER

        if self.isEqual(otherPoint):
            return 0
        explored = []
        queue = [[0, self]]

        def isVisited(element, visitedList):
            for queueElement in visitedList:
                if queueElement.isEqual(element):
                    return True
            return False

        while queue:
            path = queue.pop(0)
            node = path[-1]

            if not isVisited(node, explored):
                # debuggear("ACAAa")
                # debuggear(node.asString())
                neighbours = adjacentReachablePoints(node)
                # debuggear(list(map(lambda x : x.asString(), neighbours)))
                for neighbour in neighbours:
                    # new_path = list(path)
                    new_path = [path[0] + 1]
                    if new_path[0] > limit:
                        return BIGNUMBER
                    new_path.append(neighbour)
                    queue.append(new_path)
                    if neighbour.isEqual(otherPoint):
                        return new_path[0]
                explored.append(node)
        return BIGNUMBER

class Enemy:
    def __init__(self, number, position, type_id, abilityCd, speedTurnsLeft):
        self.number = number
        self.position = position
        self.type_id = type_id
        self.abilityCd = abilityCd
        self.speedTurnsLeft = speedTurnsLeft

class Pacman:
    def __init__(self, number, position, gameState, type_id):
        self.number = number
        self.closestPellet = None
        self.closestSuperPellet = None
        self.position = position
        self.lastPosition = Point(-1, -1)
        self.cooldown = 0
        self.regenerateRandomPoint()
        self.staticCounter = 0
        self.recentSpeed = False
        self.role = "SUPERPELLET"
        self.closestPelletDistance = BIGNUMBER
        self.closestSuperPelletDistance = BIGNUMBER
        self.superPelletObjective = None
        self.gameState = gameState
        self.type_id = type_id
        self.enemies = []
        self.enemyDistanceToReact = 2
        self.regenerateRandomPoint()
        self.closeEnemyCalculationLimit = 5
        self.farAwayDistance = int((width + height) / 6)
    
    def setType(self,type_id):
        self.type_id = type_id

    def regenerateRandomPoint(self):
        self.randomPoint = randomPoint()

    def setRole(self, role):
        self.role = role
    
    def getActionString(self):
        return self.getActionStringInternal()
        debuggear("calculo movmimiento " + str(self.number))
        a = self.getActionStringInternal()
        debuggear("devuelvo movmimiento " + str(self.number))
        return a

    def getActionStringInternal(self):
        if self.type_id == "DEAD":
            return ""

        closeEnemies = []
        closestEnemy = None
        closestEnemyDistance = BIGNUMBER
        for enemy in enemies:
            enemyPos = enemy.position
            enemyDistance = self.position.realDistance(enemyPos, self.closeEnemyCalculationLimit)
            if enemyDistance < closestEnemyDistance and enemy.type_id != "DEAD":
                closestEnemyDistance = enemyDistance
                closestEnemy = enemy
            if enemyDistance <= self.closeEnemyCalculationLimit and enemy.type_id != "DEAD":
                closeEnemies.append(enemy)
        
        if (
                self.cooldown == 0 #ability ready
        ):
            if closestEnemy is None or closestEnemyDistance > self.closeEnemyCalculationLimit:
                strategyTaken = "BOOST"
                actionString = "SPEED " + str(self.number)
                self.recentSpeed = True
                return actionString + " " + strategyTaken
            elif winner(closestEnemy.type_id) != self.type_id and closestEnemyDistance <= self.enemyDistanceToReact:
                strategyTaken = "SW"
                debuggear(self.number) 
                debuggear(closestEnemy)
                debuggear(closestEnemy.type_id)
                debuggear(winner(closestEnemy.type_id))
                actionString = "SWITCH " + str(self.number) + " " + winner(closestEnemy.type_id) 
                self.recentSpeed = True
                return actionString + " " + strategyTaken
            else:
                self.recentSpeed = False

        else: #ability on cooldown
            if closestEnemy is not None:
                #HUNT
                if winsAgainst(self.type_id, closestEnemy.type_id) and closestEnemy.abilityCd > 0 and closestEnemyDistance <= self.enemyDistanceToReact:
                    actionString = "MOVE " + str(self.number) + " " + str(closestEnemy.position.x) + " " + str(closestEnemy.position.y)
                    strategyTaken = "H"
                    self.recentSpeed = False
                    return actionString + " " + strategyTaken
                #FLEE
                elif (
                    (
                        closestEnemy.abilityCd == 0 #He can trasnform
                        or winsAgainst(closestEnemy.type_id, self.type_id) #He wins
                    )  #He wins
                 and closestEnemyDistance <= self.enemyDistanceToReact
                ): #and he is in range of killing
                    connectedPoints = adjacentReachablePoints(self.position)
                    fleePoint = None
                    for candidatePoint in connectedPoints:
                        if candidatePoint.realDistance(closestEnemy.position, self.closeEnemyCalculationLimit) > closestEnemyDistance:
                            fleePoint = candidatePoint
                            strategyTaken = "F"
                    if fleePoint is None:
                        fleePoint = self.position
                        strategyTaken = "FF"
                    actionString = "MOVE " + str(self.number) + " " + str(fleePoint.x) + " " + str(fleePoint.y)
                    self.regenerateRandomPoint()
                    self.recentSpeed = False
                    return actionString + " " + strategyTaken
                else: #I'm not close to hunt, or he is not close to kill me or we tie
                    pass
            else: #No enemies on sight
                pass


        pointsOnMap[self.position.x][self.position.y] = True # Point already visited
        strategyTaken = "UNKNOWN"


        goToPoint = self.superPelletObjective
        if goToPoint is None:
            goToPoint = self.closestPellet
            strategyTaken = "NP"
        else:
            found = False
            for sp in superPelletList:
                if sp.isEqual(self.superPelletObjective):
                    found = True
            strategyTaken = "SP"
            if not found:
                self.superPelletObjective = None
                goToPoint = self.closestPellet
                strategyTaken = "NP"

        if (
                goToPoint is None or  # No pellet on sight
                (self.lastPosition.isEqual(self.position) and not self.recentSpeed) or  # Collision blocked movement
                (goToPoint.naiveDistance(self.position) > self.farAwayDistance and  not goToPoint.isEqual(self.superPelletObjective) ) # No superPellet and objective very far away, prefer random
        ):
            goToPoint = self.randomPoint
            strategyTaken = "R"

        
        extraStep = ""
        if goToPoint.realDistance(self.position, 2) == 1:  # go one step further if distance is 1, to take advantage of superspeed
            candidates = adjacentReachablePoints(goToPoint)
            for p in candidates:
                if p.realDistance(self.position, 3) > 1:
                    extraStep = "+"
                    goToPoint = p
                    break


        moveString = "MOVE " + str(self.number) + " " + str(goToPoint.x) + " " + str(goToPoint.y)
        actionString = moveString
        self.recentSpeed = False

        return actionString + " " + strategyTaken + extraStep


    def abilityCooldown(self, cooldown):
        self.cooldown = cooldown

    def updatePosition(self, newPosition):
        self.lastPosition = self.position
        self.position = newPosition
        if self.position.isEqual(self.lastPosition):
            self.staticCounter = self.staticCounter + 1
        else:
            self.staticCounter = 0
        if self.staticCounter >= 2:
            self.regenerateRandomPoint()
        if self.position.isEqual(self.randomPoint):
            self.regenerateRandomPoint()

    def pacmanState(self):
        cadena = []
        cadena.append("pacnum: ")
        cadena.append(self.number)
        cadena.append(", position: ")
        cadena.append(self.position.asString())
        cadena.append("strat: " + self.role)
        cadena.append(" superpel: ")
        if self.superPelletObjective is not None:
            cadena.append(self.superPelletObjective.asString())
        else:
            cadena.append("None")
        cadena.append(", normalpel: ")
        if self.closestPellet is not None:
            cadena.append(self.closestPellet.x)
            cadena.append(",")
            cadena.append(self.closestPellet.y)
        else:
            cadena.append("None")
        cadena.append(", CD: ")
        cadena.append(self.cooldown)
        return reduce(lambda x, y: str(x) + str(y), cadena)
    
    def setSuperPelletObjective(self, newPoint):
        self.superPelletObjective = newPoint

#    def addInfoOnSuperPelletPoint(self, newPoint):
#        if self.closestSuperPellet is None:
#            self.closestSuperPellet = newPoint
#            self.closestSuperPelletDistance = self.position.distance(newPoint)
#        else:
#            oldDistance = self.closestSuperPelletDistance
#            if self.position.naiveDistance(newPoint) < oldDistance:
#                newDistance = self.position.distance(newPoint)
#                if newDistance < oldDistance:
#                    self.closestSuperPellet = newPoint
#                    self.closestSuperPelletDistance = newDistance

    def addInfoOnEnemies(self, enemies):
        self.enemies = enemies

    def addInfoOnPelletPoint(self, newPoint):
        if self.superPelletObjective is not None:
            return
        if self.closestPellet is None:
            self.closestPellet = newPoint
            self.closestPelletDistance = self.position.distance(newPoint)  # could be realDistance
        else:
            oldDistance = self.closestPelletDistance
            if (newPoint.x == self.position.x or newPoint.y == self.position.y):
                if oldDistance > self.position.naiveDistance(newPoint):
                    newDistance = self.position.distance(newPoint)  # Could be real realDistance
                    if newDistance < oldDistance:
                        self.closestPellet = newPoint
                        self.closestPelletDistance = newDistance

    def cleanPelletInfo(self):
        self.closestPellet = None
        self.closestSuperPellet = None


# game loop
# debuggear("A")
myPacmans = []
instantiatePacmans = True
firstTurn = True
gameState = GameState()
superPelletCount = 0
while True:
    enemies = []
    my_score, opponent_score = [int(i) for i in input().split()]
    visible_pac_count = int(input())  # all your pacs and enemy pacs in sight
    available_pacs_ids = []
    for i in range(visible_pac_count):
        # pac_id: pac number (unique within a team)
        # mine: true if this pac is yours
        # x: position in the grid
        # y: position in the grid
        # type_id: unused in wood leagues
        # speed_turns_left: unused in wood leagues
        # ability_cooldown: unused in wood leagues
        pac_id, mine, x, y, type_id, speed_turns_left, ability_cooldown = input().split()
        pac_id = int(pac_id)
        mine = mine != "0"
        x = int(x)
        y = int(y)
        speed_turns_left = int(speed_turns_left)
        ability_cooldown = int(ability_cooldown)
        if mine:
            available_pacs_ids.append(pac_id)
            if instantiatePacmans:
                newPac = Pacman(pac_id, Point(x, y), gameState, type_id)
                newPac.abilityCooldown(ability_cooldown)
                myPacmans.append(newPac)
            else:
                for pac in myPacmans:
                    pac.cleanPelletInfo()
                    if pac.number == pac_id:
                        pac.updatePosition(Point(x, y))
                        pac.abilityCooldown(ability_cooldown)
                        pac.setType(type_id)
        else:
            enemies.append( Enemy(pac_id, Point(x,y), type_id, ability_cooldown, speed_turns_left))
    instantiatePacmans = False
    visible_pellet_count = int(input())  # all pellets in sight
    for pac in myPacmans:
        if not pac.number in available_pacs_ids:
            myPacmans.remove(pac)
        else:
            pac.addInfoOnEnemies(enemies)
    
    superPelletList = []
    normalPelletList = []
    for i in range(visible_pellet_count):
        # value: amount of points this pellet is worth
        x, y, value = [int(j) for j in input().split()]
        if value > 1:
            superPelletList.append(Point(x, y))
        else:
            normalPelletList.append(Point(x, y))
    if len(superPelletList) != superPelletCount:
        gameState.setRecalculateSuperPelletObjectives(True)
    superPelletCount = len(superPelletList)


    def naiveDistanceToClosestPacman(point):
        distances = map(
            lambda pacman: pacman.position.naiveDistance(point),
            myPacmans
        )
        return min(list(distances))


    superPelletList.sort(key=naiveDistanceToClosestPacman)

    #for superPellet in superPelletPoints:
    #    def naiveDistanceToPellet(pacman):
    #        return pacman.position.naiveDistance(superPellet)
    #    myPacmans.sort(key=naiveDistanceToPellet)
    #    for p in myPacmans:
    #        p.addInfoOnSuperPelletPoint(superPellet)

    # for p in myPacmans:
    # debuggear(p.pacmanState())

    pacAndSuperPelletMatrix = []
    #for superPellet in superPelletPoints:
    #    debuggear(superPellet.asString())

    for p in myPacmans:
        if p.position.isEqual(p.superPelletObjective):
            p.superPelletObjective = None
            gameState.setRecalculateSuperPelletObjectives(True)

    if gameState.getRecalculateSuperPelletObjectives() and len(superPelletList) > 0:
        gameState.setRecalculateSuperPelletObjectives(False)
        superPelletList.sort(key=lambda point: (point.x + point.y / 100))
        myPacmans.sort(key=lambda pac: pac.number)
        #pacmansWithoutObjective = []
        for p in myPacmans:
            p.superPelletObjective = None
        distanceMatrix = []
        for i in range(len(myPacmans)):
            distanceMatrix.append([])
        for superPellet in superPelletList:
            for i in range(len(myPacmans)):
                if firstTurn:
                    distanceMatrix[i].append(myPacmans[i].position.detailedDistance(superPellet))
                else:
                    distanceMatrix[i].append(myPacmans[i].position.distance(superPellet))
        debuggear(distanceMatrix)
        usedPellets = []
        usedPacs = []
        while len(usedPacs) < len(myPacmans) and len(usedPellets) < len(superPelletList):
            pacPos = -1
            pelletPos = -1
            minDistance = BIGNUMBER + 1
            for i in range(len(distanceMatrix)):
                for j in range(len(distanceMatrix[i])):
                    if not i in usedPacs and not j in usedPellets:
                        if distanceMatrix[i][j] < minDistance:
                            minDistance = distanceMatrix[i][j]
                            pacPos = i
                            pelletPos = j
            usedPacs.append(pacPos)
            usedPellets.append(pelletPos)
            myPacmans[pacPos].setSuperPelletObjective(superPelletList[pelletPos])

        for pac in myPacmans:
            #debuggear(pac.number)
            if pac.superPelletObjective is None:
                pass
                #debuggear("None")
            else:
                pass
                #debuggear(pac.superPelletObjective.asString())
        
        #debuggear(distanceMatrix)
    for normalPellet in normalPelletList:
        for p in myPacmans:
            p.addInfoOnPelletPoint(normalPellet)

    #for p in myPacmans:
    #    for otherP in myPacmans:
    #        if p != otherP and p.role == "SUPERPELLET" and otherP.role == "SUPERPELLET":
    #            if p.closestSuperPellet is not None and otherP.closestSuperPellet is not None and p.closestSuperPellet.isEqual(
    #                    otherP.closestSuperPellet):
    #                if p.closestSuperPelletDistance < otherP.closestSuperPelletDistance:
    #                    otherP.setRole("DEFAULT")
    #                else:
    #                    p.setRole("DEFAULT")

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    # MOVE <pacId> <x> <y>
    movements = map(lambda x: x.getActionString(), myPacmans)
    movementStringCommand = reduce(lambda x, y: str(x) + '|' + str(y), movements)
    # debuggear(movementStringCommand)
    print(movementStringCommand)
    firstTurn = False

