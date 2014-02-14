(function(){
    Array.prototype.insert = function(index, value){
        this.splice(index, 0, value);
    };


    var update_time = document.getElementById('update-time');
    var list = document.getElementById('list');

    function template(info){
        var row = document.createElement('div');
        row.setAttribute('class', 'row');
        row.setAttribute('id', info.id);
        var name = document.createElement('div');
        name.setAttribute('class', 'col-md-4');
        var h2 = document.createElement('h2');
        h2.setAttribute('id', info.id + '-name');
        h2.innerText = info.line_en;
        name.appendChild(h2);
        var status = document.createElement('div');
        status.setAttribute('class', 'col-md-4');
        var strong = document.createElement('strong');
        strong.setAttribute('id', info.id + '-status');
        strong.innerText = info.status_en;
        status.appendChild(strong);
        var more = document.createElement('div');
        more.setAttribute('class', 'col-md-4');
        var small = document.createElement('small');
        small.setAttribute('id', info.id + '-more');
        small.innerText = info.more;
        more.appendChild(small);
        row.appendChild(name);
        row.appendChild(status);
        row.appendChild(more);
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

    function update(){
        var data, ele, old, item, index;
        var seen = [];
        var order = [];
        var request = new XMLHttpRequest();
        request.onreadystatechange = function(){
            if (request.readyState === 4 && request.status === 200) {
                old = document.getElementsByClassName('row');
                for (var i = 0, l = old.length; i < l; i++){
                    item = old[i];
                    order.push(item.children[0].children[0].innerText);
                }
                data = JSON.parse(request.responseText);
                for (var i = 0, l = data.lines.length; i < l; i++){
                    item = data.lines[i];
                    ele = document.getElementById(item['id'] + '-status');
                    if (ele){
                        seen.push(item['id']);
                        ele.innerText = item['status_en'];
                        ele = document.getElementById(item['id'] + '-more');
                        ele.innerText = item['more'];
                    } else {
                        ele = template(item);
                        index = find_index(order, item.line_en);
                        if (index === -1){
                            order.push(item.line_en);
                            list.appendChild(ele);
                        } else{
                            order.insert(index, item.line_en);
                            list.insertChildAfter(document.getElementsByClassName('row')[index], ele);
                        }
                    }
                }
                for (var i = 0, l = old.length; i < l; i++){
                    item = old[i];
                    if (seen.indexOf(item.getAttribute('id')) === -1){
                        item.remove();
                    }
                }
                update_time.innerText = data.updated;
                setTimeout(update, 10000);
            }
        }
        request.open('GET', '/update');
        request.send();
    };
    setTimeout(update, 10000);
})();
