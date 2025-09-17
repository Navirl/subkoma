export namespace main {
	
	export class ProcessVideoRequest {
	    input_path: string;
	    output_path: string;
	    config: string;
	
	    static createFrom(source: any = {}) {
	        return new ProcessVideoRequest(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.input_path = source["input_path"];
	        this.output_path = source["output_path"];
	        this.config = source["config"];
	    }
	}
	export class ProcessVideoResponse {
	    status: string;
	    output_video_path?: string;
	    database_id?: string;
	    message: string;
	    error_type?: string;
	
	    static createFrom(source: any = {}) {
	        return new ProcessVideoResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.status = source["status"];
	        this.output_video_path = source["output_video_path"];
	        this.database_id = source["database_id"];
	        this.message = source["message"];
	        this.error_type = source["error_type"];
	    }
	}

}

