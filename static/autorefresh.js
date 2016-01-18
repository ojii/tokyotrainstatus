(function(){
    Array.prototype.insert = function(index, value){
        this.splice(index, 0, value);
    };
    Node.prototype.clear = function(){
        while (this.firstChild){
            this.removeChild(this.firstChild);
        }
    };

    var update_time = document.getElementById('update-time');
    var list = document.getElementById('list');
    var no_issues = document.getElementById('no-issues');
    var no_connection = document.getElementById('no-connection');
    var reconnecting = null;

    function template(info){
        var row = document.createElement('div');
        row.setAttribute('class', 'list-item');
        row.setAttribute('id', info.id);

        var wrapper = document.createElement('div');
        wrapper.setAttribute('class', 'col-md-12');
        row.appendChild(wrapper);

        var h2 = document.createElement('h2');
        h2.setAttribute('id', info.id + '-name');
        h2.innerText = info.line_en;
        wrapper.appendChild(h2);

        var janame = document.createElement('small');
        janame.innerText = info.line;
        h2.appendChild(janame);

        var status = document.createElement('div');
        status.setAttribute('id', info.id + '-wrapper');
        var severity = info.severe ? 'danger' : 'warning';
        status.setAttribute('class', 'alert alert-' + severity);
        wrapper.appendChild(status);

        var strong = document.createElement('strong');
        strong.setAttribute('id', info.id + '-status');
        strong.innerText = info.status_en;
        status.appendChild(strong);

        var small = document.createElement('small');
        small.setAttribute('id', info.id + '-more');
        small.innerText = info.reason;
        status.appendChild(small);

        return row;
    }

    function find_index(arr, needle){
        for (var i = 0, l = arr.length; i < l; i++){
            if ([arr[i], needle].sort()[0] === needle){
                return i;
            }
        }
        return -1;
    }

    function _update(data){
        var data, ele, old, item, index;
        var seen = [];
        var order = [];
        old = document.getElementsByClassName('list-item');
        for (var i = 0, l = old.length; i < l; i++){
            item = old[i];
            order.push(item.children[0].children[0].innerText);
        }
        if (data.lines.length){
            no_issues.setAttribute('class', 'alert alert-success hidden');
            no_connection.setAttribute('class', 'alert alert-warning hidden');
            for (var i = 0, l = data.lines.length; i < l; i++){
                item = data.lines[i];
                ele = document.getElementById(item['id'] + '-status');
                seen.push(item['id']);
                if (ele){
                    ele.innerText = item['status_en'];
                    ele = document.getElementById(item['id'] + '-more');
                    ele.innerText = item['reason'];
                    ele = document.getElementById(item['id'] + '-wrapper');
                    if (item['severe']){
                        ele.setAttribute('class', 'alert alert-danger');
                    } else {
                        ele.setAttribute('class', 'alert alert-warning');
                    }
                } else {
                    ele = template(item);
                    index = find_index(order, item.line_en);
                    if (index === -1){
                        order.push(item.line_en);
                        list.appendChild(ele);
                    } else{
                        order.insert(index, item.line_en);
                        list.insertChildAfter(document.getElementsByClassName('list-item')[index], ele);
                    }
                }
            }
            old = document.getElementsByClassName('list-item');
            for (var i = 0, l = old.length; i < l; i++){
                item = old[i];
                if (seen.indexOf(item.getAttribute('id')) === -1){
                    item.remove();
                }
            }
        } else {
            if (data.live){
                no_issues.setAttribute('class', 'alert alert-success');
                no_connection.setAttribute('class', 'alert alert-warning hidden');
            } else {
                no_connection.setAttribute('class', 'alert alert-warning');
                no_issues.setAttribute('class', 'alert alert-success hidden');
            }
            list.clear();
        }
        update_time.innerText = data.updated;
    }

    function update(){
        var request = new XMLHttpRequest();
        request.onreadystatechange = function(){
            if (request.readyState === 4 && request.status === 200) {
                _update(JSON.parse(request.responseText));
                setTimeout(update, 10000);
            }
        }
        request.onerror = function(){
            reconnect();
        };
        request.open('GET', '/update');
        request.send();
    };

    function connect(){
        reconnecting = null;
        if (window.WebSocket){
            var protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            var socket = new WebSocket(protocol + '://' + window.location.host + '/ws/');
            socket.onmessage = function(event){
                _update(JSON.parse(event.data));
            };

            socket.onclose = function(event){
                reconnect();
            };

            socket.onerror = function(event){
                reconnect();
            };
        } else {
            setTimeout(update, 10000);
        }
    }

    function reconnect(){
        if (reconnecting !== null){
            return;
        }
        update_time.innerText = 'Reconnecting...';
        reconnecting = setTimeout(connect, 10000);
    }

    connect();
})();
