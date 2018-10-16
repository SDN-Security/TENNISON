class ChartData{

	constructor(){

		this.data = {};
	}

	getDict(){ return this.data; }
	get(i){
		if(i in this.data){
	//		console.log("In dict");
			return this.data[i];
		} else {

			this.data[i] = new Src(i);
			return this.data[i];
		}
	}

}
class HostSrc{

	constructor(name){
		this.name = name;
		this.dests = {};
		this.ports = {};
	}
	add(dest, port){
		if(dest in this.dests){

			this.dests[dest] += 1;
		} else {
			this.dests[dest] = 1;

		}
		if(port in this.ports){
			this.ports[port] += 1;
		} else {
			this.ports[port] = 1;
		}

	}
	getNumDests(i){
		return this.dests[i];
	}
	getDestDict(){
		return this.dests;

	}

}
class Src{


	constructor(name){
		this.name = name;
		this.dests = [];
		this.ports = [];
	}

	add(dst,port){
		this.dests.push(dst);
		this.ports.push(port);
	}
        getUniqueDests(){


        }
	getAllDests(){
		return this.dests;
	}
	getAllPorts(){
		return this.ports;
	}

}
