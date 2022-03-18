#!/bin/env python3

import random
import math
from dataclasses import dataclass
import sys
from matplotlib import pyplot as plt

def Roll():
    res = 0
    dice = random.randint(1,6)
    res += dice
    while(dice == 6):
        dice = random.randint(1,6)
        res += dice

    return res;

class State:
    Okay = 0
    Low = 1
    Eliminated = 2

class Fighter:
    def __init__(self,name,hp,atk,deff,bon):
        self.Name = name
        self.HealthMax = hp
        self.HealthCurrent = self.HealthMax
        self.Thresh = math.ceil(self.HealthMax/3) #Todo: This should not affect characters with extra max hp (their low threshold should be the same for all)
        self.DefenseVal = deff
        self.AttackStr = atk
        self.BonusDmg = bon

    def __repr__(self):
        rec = f"Bojovník {self.Name}:\n" \
        + f"Životy: {self.HealthCurrent}/{self.HealthMax}\n"\
        + f"Útok: {self.AttackStr}/{self.BonusDmg}\n"\
        + f"Obrana: {self.DefenseVal}\n"\
        
        return rec;

    def GetState(self):
        if self.HealthCurrent <= 1:
            return State.Eliminated;
        elif self.HealthCurrent < self.Thresh:
            return State.Low;
        else:
            return State.Okay;

    def CalcAtk(self):
        roll = Roll()
        atk = roll
        if self.HealthCurrent < self.Thresh:
            atk -= 1
        atk += max(self.AttackStr,0)
        return atk;

    def CalcDef(self):
        roll = Roll()
        deff = roll
        if self.HealthCurrent < self.Thresh:
            deff -= 1
        deff += max (self.DefenseVal,0)
        return deff;

    def Attack(self,enemy:'Fighter'):
        atkValue = self.CalcAtk()
        defValue = enemy.CalcDef()
        damage = 0
        if (atkValue > defValue):
            damage = max(atkValue - defValue + self.BonusDmg, 1)
        enemy.HealthCurrent = max(enemy.HealthCurrent - damage, 1)
        return damage, enemy.GetState()

    def GetPriority(self): #priority of others attacking this target
        hperc = self.HealthCurrent/self.HealthMax
        rng = random.random()
        return hperc + rng

#Záznam soubojů jednoho kola
class Round():
    def __init__(self,previous:'Round'=None,fighters:list=None):
        
        if previous:
            self.lastFP = previous.GetLast()
            self.fighters = [f for f in previous.fighters if f.GetState() != State.Eliminated]
        else:
            self.lastFP = None
            self.fighters = fighters
            assert(fighters!=None)

        self.attacks = [] #Attacks = kdo na koho útočil a za kolik

    def GetLast(self):
        return self.attacks[-1][0]

    def SortAttackers(self):
        fighters = self.fighters
        fighters.sort(key=lambda x: random.random())
        if fighters[0].Name == self.lastFP: #No double atk: assume the player has checked the Dl at another random time when somebody attacked already
            first = fighters.pop()
            if len(fighters) <= 1:
                position = 0
            else:
                position = random.randint(0,len(fighters)-1)

            if position == 0:
                fighters.append(first) #Put at last
            else:
                fighters.insert(position,first)

    #Vyber nejvhodnější cíl
    def PickTarget(self,fighter):
        assert(fighter.GetState()!=State.Eliminated)
        prio = -2**10
        chosen = None
        cid = -100
        f:Fighter
        for id,f in enumerate(self.fighters):
            if f.Name == fighter.Name:
                continue
            if f.GetState()==State.Eliminated:
                continue
            priority = f.GetPriority()
            if priority > prio:
                chosen = f
                cid = id
                prio = priority
        return cid,chosen

    #Vybere útočníky v náhodném pořadí. Útoky se vyhodnocují hned, ne všechny najednou
    def Simulate(self):
        self.SortAttackers()
        A:Fighter
        D:Fighter
        for A in self.fighters:
            if (A.GetState()==State.Eliminated):
                continue
            _,D = self.PickTarget(A)
            if not D: #Není na koho útočit
                return
            dmg,state = A.Attack(D)
            self.attacks.append( (A.Name,D.Name,dmg) )
        return 


#Simulace celého souboje, momentálně mají všichni stejně zdraví (parametr "verbose" vypisuje stav po jednotlivých kolech)
def OneFight(FighterCount,Health,Attack,Defense,Bonus,Names,verbose=False):
    assert(len(Names)>=FighterCount)
    Fighters = [Fighter(Names[i],Health,Attack,Defense,Bonus) for i in range(FighterCount)]

    if(verbose):
        for f in Fighters:
            print(f)
            continue
        print("-"*20+"\n")

    LastRound = None
    rounds = []

    while((not LastRound) or (len(LastRound.fighters)>1) ):
        if not LastRound:
            NewRound = Round(None,Fighters)
        else:
            NewRound = Round(LastRound)
        NewRound.Simulate()
        rounds.append(NewRound)
        LastRound = NewRound
        if(verbose):
            for f in sorted(LastRound.fighters,key=lambda x: x.Name):
                print(f)
            print("-"*20 + "\n")
        

    if(verbose):
        print("Počet kol:",len(rounds))
    return LastRound.fighters[0],len(rounds)

#Spočítá více soubojů, počet výher pro jednotlivé hráče a průměrnou délku
def EvalSims(FighterCount,Health,Attack,Defense,Bonus):
    Names = "ABCDEFGHIJKLMN"

    print("Počet:",FighterCount)
    print("Zdraví:",Health)
    print("Síla:",Attack)
    print("Obrana:",Defense)
    print("Útočnost:",Bonus)
    total = 0
    simulations = 1000
    winners = {}
    for i in range(simulations):
        winning,rounds = OneFight(FighterCount,Health,Attack,Defense,Bonus,Names,False)
        dwin = winners.get(winning.Name,0)
        dwin += 1
        winners[winning.Name]=dwin
        total += rounds
    print("Průměr:",total/simulations)
    print("---")
    winners = sorted(winners.items())
    for name,wins in winners:
        print(f"{name}:{wins}")
    print("---\n")
    return winners, total/simulations

def LeastSquareDiff(f1,f2): #Assuming the x are same
    assert len(f1) == len(f2)
    diff = 0
    for i in range(len(f1)):
        y1 = f1[i]
        y2 = f2[i]
        dist = (y1-y2) ** 2
        diff += dist
    return diff

def CalcVar(lst):
    avg = sum(lst)/len(lst)
    return sum ((it-avg)**2 for it in lst)

#Běží souboje s různými parametry, vabere ten s nejmeněím rozptylem 
def CompareFights():
    counts = list(range(2,10+1))
    bestTotalVariance = 2**30
    bestVals = (None,None,None,None)
    bestAvgs = []
    bestWinCounts = None

    try:
        for Health in range(10,30+1):
            for Attack in range(0,4+1):
                for Defense in range(0,1): #In this case, only the A-D really matters since we do not introduce any extra bonuses
                    for Bonus in range(0,1+1):
                        avgs = [] 
                        winning = []
                        normalized = []
                        for FighterCount in counts:
                            winners,avg = EvalSims(FighterCount,Health,Attack,Defense,Bonus)
                            avgs.append(avg)
                            winning.append([w[1] for w in winners])
                            normalized.append([w[1] * FighterCount/counts[-1] for w in winners]) #Normalize the wins relatively to amount of players
                        vars = [CalcVar(nw) for nw in normalized]
                        totalVariance = sum(v*v for v in vars)
                        if totalVariance < bestTotalVariance:
                            bestTotalVariance = totalVariance
                            bestVals = (Health,Attack,Defense,Bonus) #Change this when the extra bonuses get introduced
                            bestWinCounts = winning
    except KeyboardInterrupt:
        pass
    except:
        raise
    finally:
        print(bestVals)
        print(bestWinCounts)
        print(bestAvgs)
        print(bestTotalVariance)


def main():
    #CompareFights()
    FighterCount = 5
    Health = 17
    Attack = 4
    Defense = 3
    Bonus = 1
    winners, average = EvalSims(FighterCount,Health,Attack,Defense,Bonus)
    print(winners,average)
    
if __name__ == "__main__":
    main()
