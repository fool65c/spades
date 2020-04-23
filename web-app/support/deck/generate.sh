for suit in $(echo clubs diamonds hearts spades); do
for i in $(echo $(seq 2 10) A K Q J); do
if [[ "${suit}" == "diamonds" ]]; then
s="♦️"
fi
if [[ "${suit}" == "hearts" ]]; then
s="♥️"
fi
if [[ "${suit}" == "clubs" ]]; then
s="♣️"
fi
if [[ "${suit}" == "spades" ]]; then
s="♠️"
fi

i2=$i
if [[ "$i" == "A" ]]; then
i2="Ace"
fi
if [[ "$i" == "K" ]]; then
i2="King"
fi
if [[ "$i" == "Q" ]]; then
i2="Queen"
fi
if [[ "$i" == "J" ]]; then
i2="Jack"
fi

echo .${s}${i}-small '{ background: url(/support/deck/'${suit}.${i2}'.svg); height: 40px; width: 30px;}'
done
done
