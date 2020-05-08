let GameFeed = class {
    constructor() {
        var url = window.location.href;
        var arr = url.split("/");

        if (location.protocol !== 'https:') {
            this.endpoint = "ws://" + arr[2] + "/updates"
        } else {
            this.endpoint = "wss://" + arr[2] + "/updates"
        }

        this.playerName = '';
        this.id = '';
        this.gameId = '';
        this.callbacks = {}
        this.connect()
    }

    connect() {
        let that = this;

        this.webSocket = new WebSocket(this.endpoint);
        this.webSocket.onopen = function(event) {
            that.onOpen(that, event);
        }
        this.webSocket.onmessage = function(event) {
            that.onMessage(that, event);
        }

        this.webSocket.onclose = function(event) {
            console.log(event);
            setTimeout(function() {
                that.connect();
              }, 1000);
        }
    }

    onOpen(gameFeed, event) {
        console.log("ws connection open", event);
    
        let playerName = getCookie("playerName");
        let playerId = getCookie("playerId");
        console.log('rejoin', playerName, playerId)
        if (playerName == '' && playerId == '') {
            console.log('start over')
            gameFeed.send("register-player");
            $('#playerSignin').modal('show')
        } else {
            $('#playerSignin').modal('hide');
            gameFeed.playerName = playerName;
            gameFeed.id = playerId;
            gameFeed.send('player-rejoin', playerName)
        }
    }

    onMessage(gameFeed, event) {
        console.log("gameFeed.onMessage:", event.data)
        let data = JSON.parse(event.data)
        if ('type' in data && data.type in gameFeed.callbacks) {
            this.callbacks[data.type](data)
        } else {
            console.log("unknown message", data)
        }
    }

    send(type, message) {
        console.log(type, message)
        this.webSocket.send(JSON.stringify({
            type: type,
            id: this.id,
            game_id: this.gameId,
            message: message
        }))
    }

    register(type, callback) {
        this.callbacks[type] = callback;
    }
}