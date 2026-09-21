export namespace container {
	
	export class Container {
	    id: string;
	    name: string;
	    image: string;
	    state: string;
	    status: string;
	    ports: string;
	    createdAt: string;
	
	    static createFrom(source: any = {}) {
	        return new Container(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.image = source["image"];
	        this.state = source["state"];
	        this.status = source["status"];
	        this.ports = source["ports"];
	        this.createdAt = source["createdAt"];
	    }
	}
	export class Mount {
	    source: string;
	    destination: string;
	    rw: boolean;
	
	    static createFrom(source: any = {}) {
	        return new Mount(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.source = source["source"];
	        this.destination = source["destination"];
	        this.rw = source["rw"];
	    }
	}
	export class PortMapping {
	    hostIp?: string;
	    hostPort: string;
	    containerPort: string;
	    protocol: string;
	
	    static createFrom(source: any = {}) {
	        return new PortMapping(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.hostIp = source["hostIp"];
	        this.hostPort = source["hostPort"];
	        this.containerPort = source["containerPort"];
	        this.protocol = source["protocol"];
	    }
	}
	export class ContainerDetail {
	    id: string;
	    name: string;
	    image: string;
	    state: string;
	    status: string;
	    startedAt: string;
	    finishedAt: string;
	    exitCode?: number;
	    oomKilled: boolean;
	    pid: number;
	    restartPolicy: string;
	    entrypoint: string;
	    command: string;
	    workDir: string;
	    user: string;
	    networkMode: string;
	    ip: string;
	    gateway: string;
	    ports: PortMapping[];
	    mounts: Mount[];
	    env: string[];
	
	    static createFrom(source: any = {}) {
	        return new ContainerDetail(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.image = source["image"];
	        this.state = source["state"];
	        this.status = source["status"];
	        this.startedAt = source["startedAt"];
	        this.finishedAt = source["finishedAt"];
	        this.exitCode = source["exitCode"];
	        this.oomKilled = source["oomKilled"];
	        this.pid = source["pid"];
	        this.restartPolicy = source["restartPolicy"];
	        this.entrypoint = source["entrypoint"];
	        this.command = source["command"];
	        this.workDir = source["workDir"];
	        this.user = source["user"];
	        this.networkMode = source["networkMode"];
	        this.ip = source["ip"];
	        this.gateway = source["gateway"];
	        this.ports = this.convertValues(source["ports"], PortMapping);
	        this.mounts = this.convertValues(source["mounts"], Mount);
	        this.env = source["env"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class CreateOptions {
	    image: string;
	    name: string;
	    ports: PortMapping[];
	    volumes: string[];
	    env: string[];
	    restart: string;
	    command: string[];
	
	    static createFrom(source: any = {}) {
	        return new CreateOptions(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.image = source["image"];
	        this.name = source["name"];
	        this.ports = this.convertValues(source["ports"], PortMapping);
	        this.volumes = source["volumes"];
	        this.env = source["env"];
	        this.restart = source["restart"];
	        this.command = source["command"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class Image {
	    id: string;
	    repository: string;
	    tag: string;
	    size: string;
	    createdAt: string;
	
	    static createFrom(source: any = {}) {
	        return new Image(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.repository = source["repository"];
	        this.tag = source["tag"];
	        this.size = source["size"];
	        this.createdAt = source["createdAt"];
	    }
	}
	export class InspectResult {
	    detail: ContainerDetail;
	    raw: string;
	
	    static createFrom(source: any = {}) {
	        return new InspectResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.detail = this.convertValues(source["detail"], ContainerDetail);
	        this.raw = source["raw"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	
	
	export class Stats {
	    id: string;
	    name: string;
	    cpuPercent: string;
	    memUsage: string;
	    memPercent: string;
	    netIO: string;
	    blockIO: string;
	
	    static createFrom(source: any = {}) {
	        return new Stats(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.cpuPercent = source["cpuPercent"];
	        this.memUsage = source["memUsage"];
	        this.memPercent = source["memPercent"];
	        this.netIO = source["netIO"];
	        this.blockIO = source["blockIO"];
	    }
	}

}

export namespace database {
	
	export class ColumnDef {
	    name: string;
	    type: string;
	    nullable: boolean;
	    defaultVal: string;
	    defaultType: string;
	    comment: string;
	    collation: string;
	    onUpdate: boolean;
	
	    static createFrom(source: any = {}) {
	        return new ColumnDef(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.type = source["type"];
	        this.nullable = source["nullable"];
	        this.defaultVal = source["defaultVal"];
	        this.defaultType = source["defaultType"];
	        this.comment = source["comment"];
	        this.collation = source["collation"];
	        this.onUpdate = source["onUpdate"];
	    }
	}
	export class ColumnInfo {
	    name: string;
	    type: string;
	    nullable: boolean;
	    defaultVal: string;
	    defaultType: string;
	    isPrimary: boolean;
	    comment: string;
	    collation: string;
	    onUpdate: boolean;
	
	    static createFrom(source: any = {}) {
	        return new ColumnInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.type = source["type"];
	        this.nullable = source["nullable"];
	        this.defaultVal = source["defaultVal"];
	        this.defaultType = source["defaultType"];
	        this.isPrimary = source["isPrimary"];
	        this.comment = source["comment"];
	        this.collation = source["collation"];
	        this.onUpdate = source["onUpdate"];
	    }
	}
	export class ExecResult {
	    affected: number;
	    lastInsertId: number;
	
	    static createFrom(source: any = {}) {
	        return new ExecResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.affected = source["affected"];
	        this.lastInsertId = source["lastInsertId"];
	    }
	}
	export class IndexDef {
	    name: string;
	    columns: string[];
	    unique: boolean;
	    isPrimary: boolean;
	
	    static createFrom(source: any = {}) {
	        return new IndexDef(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.columns = source["columns"];
	        this.unique = source["unique"];
	        this.isPrimary = source["isPrimary"];
	    }
	}
	export class IndexInfo {
	    name: string;
	    columns: string[];
	    unique: boolean;
	    isPrimary: boolean;
	
	    static createFrom(source: any = {}) {
	        return new IndexInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.columns = source["columns"];
	        this.unique = source["unique"];
	        this.isPrimary = source["isPrimary"];
	    }
	}
	export class QueryResultColumn {
	    name: string;
	    type: string;
	
	    static createFrom(source: any = {}) {
	        return new QueryResultColumn(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.type = source["type"];
	    }
	}
	export class QueryResult {
	    columns: QueryResultColumn[];
	    rows: any[];
	
	    static createFrom(source: any = {}) {
	        return new QueryResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.columns = this.convertValues(source["columns"], QueryResultColumn);
	        this.rows = source["rows"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	
	export class SchemaResult {
	    columns: ColumnInfo[];
	    indexes: IndexInfo[];
	
	    static createFrom(source: any = {}) {
	        return new SchemaResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.columns = this.convertValues(source["columns"], ColumnInfo);
	        this.indexes = this.convertValues(source["indexes"], IndexInfo);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class ScriptResult {
	    executed: number;
	    failedLine: number;
	    failedSql: string;
	    error: string;
	    affectedTotal: number;
	
	    static createFrom(source: any = {}) {
	        return new ScriptResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.executed = source["executed"];
	        this.failedLine = source["failedLine"];
	        this.failedSql = source["failedSql"];
	        this.error = source["error"];
	        this.affectedTotal = source["affectedTotal"];
	    }
	}
	export class TableInfo {
	    name: string;
	    type: string;
	    comment: string;
	
	    static createFrom(source: any = {}) {
	        return new TableInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.type = source["type"];
	        this.comment = source["comment"];
	    }
	}

}

export namespace importer {
	
	export class ImportResult {
	    groups: session.ConnectionGroup[];
	    connections: session.ConnectionConfig[];
	    warnings: string[];
	
	    static createFrom(source: any = {}) {
	        return new ImportResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.groups = this.convertValues(source["groups"], session.ConnectionGroup);
	        this.connections = this.convertValues(source["connections"], session.ConnectionConfig);
	        this.warnings = source["warnings"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

export namespace k8s {
	
	export class ContextInfo {
	    name: string;
	    cluster: string;
	    user: string;
	    namespace: string;
	    current: boolean;
	
	    static createFrom(source: any = {}) {
	        return new ContextInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.cluster = source["cluster"];
	        this.user = source["user"];
	        this.namespace = source["namespace"];
	        this.current = source["current"];
	    }
	}

}

export namespace main {
	
	export class AppInfo {
	    name: string;
	    version: string;
	
	    static createFrom(source: any = {}) {
	        return new AppInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.version = source["version"];
	    }
	}
	export class CredentialStatus {
	    mode: string;
	    unlocked: boolean;
	    needsSetup: boolean;
	    keychainLost: boolean;
	    existingSecrets: number;
	
	    static createFrom(source: any = {}) {
	        return new CredentialStatus(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.mode = source["mode"];
	        this.unlocked = source["unlocked"];
	        this.needsSetup = source["needsSetup"];
	        this.keychainLost = source["keychainLost"];
	        this.existingSecrets = source["existingSecrets"];
	    }
	}
	export class DataDirInfo {
	    dataDir: string;
	    type: string;
	    firstRun: boolean;
	
	    static createFrom(source: any = {}) {
	        return new DataDirInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.dataDir = source["dataDir"];
	        this.type = source["type"];
	        this.firstRun = source["firstRun"];
	    }
	}
	export class K8sResponse {
	    status: number;
	    body: string;
	
	    static createFrom(source: any = {}) {
	        return new K8sResponse(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.status = source["status"];
	        this.body = source["body"];
	    }
	}
	export class ModelInfo {
	    id: string;
	    display_name: string;
	
	    static createFrom(source: any = {}) {
	        return new ModelInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.display_name = source["display_name"];
	    }
	}
	export class SessionLogInfo {
	    enabled: boolean;
	    path: string;
	
	    static createFrom(source: any = {}) {
	        return new SessionLogInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.enabled = source["enabled"];
	        this.path = source["path"];
	    }
	}

}

export namespace platform {
	
	export class FontInfo {
	    Name: string;
	    IsMono: boolean;
	
	    static createFrom(source: any = {}) {
	        return new FontInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.Name = source["Name"];
	        this.IsMono = source["IsMono"];
	    }
	}

}

export namespace session {
	
	export class PostLoginExpectStep {
	    expect: string;
	    send: string;
	    enter: boolean;
	    timeoutSecond?: number;
	
	    static createFrom(source: any = {}) {
	        return new PostLoginExpectStep(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.expect = source["expect"];
	        this.send = source["send"];
	        this.enter = source["enter"];
	        this.timeoutSecond = source["timeoutSecond"];
	    }
	}
	export class ConnectionConfig {
	    id: string;
	    name: string;
	    remark?: string;
	    type: string;
	    host: string;
	    port: number;
	    user: string;
	    authType: string;
	    kerberosRealm?: string;
	    identityId?: string;
	    password?: string;
	    keyPath?: string;
	    groupId?: string;
	    rdpFixedWidth?: number;
	    rdpFixedHeight?: number;
	    rdpSmartSizing: boolean;
	    rdpEnableNLA: boolean;
	    shellPath?: string;
	    cwd?: string;
	    serialPort?: string;
	    serialBaudRate?: number;
	    serialDataBits?: number;
	    serialStopBits?: number;
	    serialParity?: string;
	    dbType?: string;
	    dbName?: string;
	    dbParams?: string;
	    esUseSsl?: boolean;
	    esPathPrefix?: string;
	    esSkipVerify?: boolean;
	    redisMode?: string;
	    redisMasterName?: string;
	    redisSentinels?: string;
	    sentinelUser?: string;
	    sentinelPassword?: string;
	    postLoginScript?: string;
	    postLoginExpectSteps?: PostLoginExpectStep[];
	    tunnelSSHConnId?: string;
	    proxyId?: string;
	    tunnelSSHUser?: string;
	    tunnelSSHPassword?: string;
	    sftpMaxConcurrency?: number;
	    initialCols?: number;
	    initialRows?: number;
	    ftpEncryption?: string;
	    ftpPassive: boolean;
	    ftpEncoding?: string;
	    ftpSkipVerify?: boolean;
	    vncShared?: boolean;
	    vncRepeaterID?: string;
	    smbDomain?: string;
	    smbShare?: string;
	    s3Region?: string;
	    s3Bucket?: string;
	    s3UrlStyle?: string;
	    encoding?: string;
	    x11Forwarding?: boolean;
	    agentForwarding?: boolean;
	    backspaceKey?: string;
	    telnetNegotiationMode?: string;
	    localEcho?: boolean;
	    telnetSendMode?: string;
	    newlineMode?: string;
	    k8sConfigPath?: string;
	    k8sConfigInline?: string;
	    k8sContext?: string;
	    k8sNamespace?: string;
	    k8sInsecureTls?: boolean;
	    containerTransport?: string;
	    containerSSHConnId?: string;
	    containerRuntime?: string;
	    logOnConnect?: boolean;
	    x11DesktopDesktopType?: string;
	    x11DesktopCustomCmd?: string;
	
	    static createFrom(source: any = {}) {
	        return new ConnectionConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.remark = source["remark"];
	        this.type = source["type"];
	        this.host = source["host"];
	        this.port = source["port"];
	        this.user = source["user"];
	        this.authType = source["authType"];
	        this.kerberosRealm = source["kerberosRealm"];
	        this.identityId = source["identityId"];
	        this.password = source["password"];
	        this.keyPath = source["keyPath"];
	        this.groupId = source["groupId"];
	        this.rdpFixedWidth = source["rdpFixedWidth"];
	        this.rdpFixedHeight = source["rdpFixedHeight"];
	        this.rdpSmartSizing = source["rdpSmartSizing"];
	        this.rdpEnableNLA = source["rdpEnableNLA"];
	        this.shellPath = source["shellPath"];
	        this.cwd = source["cwd"];
	        this.serialPort = source["serialPort"];
	        this.serialBaudRate = source["serialBaudRate"];
	        this.serialDataBits = source["serialDataBits"];
	        this.serialStopBits = source["serialStopBits"];
	        this.serialParity = source["serialParity"];
	        this.dbType = source["dbType"];
	        this.dbName = source["dbName"];
	        this.dbParams = source["dbParams"];
	        this.esUseSsl = source["esUseSsl"];
	        this.esPathPrefix = source["esPathPrefix"];
	        this.esSkipVerify = source["esSkipVerify"];
	        this.redisMode = source["redisMode"];
	        this.redisMasterName = source["redisMasterName"];
	        this.redisSentinels = source["redisSentinels"];
	        this.sentinelUser = source["sentinelUser"];
	        this.sentinelPassword = source["sentinelPassword"];
	        this.postLoginScript = source["postLoginScript"];
	        this.postLoginExpectSteps = this.convertValues(source["postLoginExpectSteps"], PostLoginExpectStep);
	        this.tunnelSSHConnId = source["tunnelSSHConnId"];
	        this.proxyId = source["proxyId"];
	        this.tunnelSSHUser = source["tunnelSSHUser"];
	        this.tunnelSSHPassword = source["tunnelSSHPassword"];
	        this.sftpMaxConcurrency = source["sftpMaxConcurrency"];
	        this.initialCols = source["initialCols"];
	        this.initialRows = source["initialRows"];
	        this.ftpEncryption = source["ftpEncryption"];
	        this.ftpPassive = source["ftpPassive"];
	        this.ftpEncoding = source["ftpEncoding"];
	        this.ftpSkipVerify = source["ftpSkipVerify"];
	        this.vncShared = source["vncShared"];
	        this.vncRepeaterID = source["vncRepeaterID"];
	        this.smbDomain = source["smbDomain"];
	        this.smbShare = source["smbShare"];
	        this.s3Region = source["s3Region"];
	        this.s3Bucket = source["s3Bucket"];
	        this.s3UrlStyle = source["s3UrlStyle"];
	        this.encoding = source["encoding"];
	        this.x11Forwarding = source["x11Forwarding"];
	        this.agentForwarding = source["agentForwarding"];
	        this.backspaceKey = source["backspaceKey"];
	        this.telnetNegotiationMode = source["telnetNegotiationMode"];
	        this.localEcho = source["localEcho"];
	        this.telnetSendMode = source["telnetSendMode"];
	        this.newlineMode = source["newlineMode"];
	        this.k8sConfigPath = source["k8sConfigPath"];
	        this.k8sConfigInline = source["k8sConfigInline"];
	        this.k8sContext = source["k8sContext"];
	        this.k8sNamespace = source["k8sNamespace"];
	        this.k8sInsecureTls = source["k8sInsecureTls"];
	        this.containerTransport = source["containerTransport"];
	        this.containerSSHConnId = source["containerSSHConnId"];
	        this.containerRuntime = source["containerRuntime"];
	        this.logOnConnect = source["logOnConnect"];
	        this.x11DesktopDesktopType = source["x11DesktopDesktopType"];
	        this.x11DesktopCustomCmd = source["x11DesktopCustomCmd"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class ConnectionGroup {
	    id: string;
	    name: string;
	    parentId?: string;
	
	    static createFrom(source: any = {}) {
	        return new ConnectionGroup(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.parentId = source["parentId"];
	    }
	}
	export class ConnectionStoreData {
	    groups: ConnectionGroup[];
	    connections: ConnectionConfig[];
	
	    static createFrom(source: any = {}) {
	        return new ConnectionStoreData(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.groups = this.convertValues(source["groups"], ConnectionGroup);
	        this.connections = this.convertValues(source["connections"], ConnectionConfig);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class DiskInfo {
	    name: string;
	    type: string;
	    size: string;
	    mountPoint: string;
	    used: string;
	    total: string;
	    usage: number;
	    media: string;
	    fsType: string;
	    uuid: string;
	    vendor: string;
	    model: string;
	
	    static createFrom(source: any = {}) {
	        return new DiskInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.type = source["type"];
	        this.size = source["size"];
	        this.mountPoint = source["mountPoint"];
	        this.used = source["used"];
	        this.total = source["total"];
	        this.usage = source["usage"];
	        this.media = source["media"];
	        this.fsType = source["fsType"];
	        this.uuid = source["uuid"];
	        this.vendor = source["vendor"];
	        this.model = source["model"];
	    }
	}
	export class EsClusterHealth {
	    clusterName: string;
	    status: string;
	    numberOfNodes: number;
	    numberOfDataNodes: number;
	    activePrimaryShards: number;
	    activeShards: number;
	    relocatingShards: number;
	    initializingShards: number;
	    unassignedShards: number;
	
	    static createFrom(source: any = {}) {
	        return new EsClusterHealth(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.clusterName = source["clusterName"];
	        this.status = source["status"];
	        this.numberOfNodes = source["numberOfNodes"];
	        this.numberOfDataNodes = source["numberOfDataNodes"];
	        this.activePrimaryShards = source["activePrimaryShards"];
	        this.activeShards = source["activeShards"];
	        this.relocatingShards = source["relocatingShards"];
	        this.initializingShards = source["initializingShards"];
	        this.unassignedShards = source["unassignedShards"];
	    }
	}
	export class EsClusterInfo {
	    name: string;
	    clusterName: string;
	    clusterUUID: string;
	    version: string;
	    tagline: string;
	
	    static createFrom(source: any = {}) {
	        return new EsClusterInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.clusterName = source["clusterName"];
	        this.clusterUUID = source["clusterUUID"];
	        this.version = source["version"];
	        this.tagline = source["tagline"];
	    }
	}
	export class EsIndexInfo {
	    name: string;
	    health: string;
	    status: string;
	    docsCount: number;
	    storeSize: string;
	    pri: number;
	    rep: number;
	
	    static createFrom(source: any = {}) {
	        return new EsIndexInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.health = source["health"];
	        this.status = source["status"];
	        this.docsCount = source["docsCount"];
	        this.storeSize = source["storeSize"];
	        this.pri = source["pri"];
	        this.rep = source["rep"];
	    }
	}
	export class EsNodeSummary {
	    name: string;
	    ip: string;
	    nodeRole: string;
	    heapPercent: string;
	    ramPercent: string;
	    cpu: string;
	    load1m: string;
	    master: string;
	
	    static createFrom(source: any = {}) {
	        return new EsNodeSummary(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.ip = source["ip"];
	        this.nodeRole = source["nodeRole"];
	        this.heapPercent = source["heapPercent"];
	        this.ramPercent = source["ramPercent"];
	        this.cpu = source["cpu"];
	        this.load1m = source["load1m"];
	        this.master = source["master"];
	    }
	}
	export class EsRestResult {
	    status: number;
	    body: string;
	
	    static createFrom(source: any = {}) {
	        return new EsRestResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.status = source["status"];
	        this.body = source["body"];
	    }
	}
	export class EsSearchResult {
	    hits: string[];
	    total: number;
	    from: number;
	    size: number;
	    took: number;
	
	    static createFrom(source: any = {}) {
	        return new EsSearchResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.hits = source["hits"];
	        this.total = source["total"];
	        this.from = source["from"];
	        this.size = source["size"];
	        this.took = source["took"];
	    }
	}
	export class FieldEntry {
	    field: string;
	    value: string;
	
	    static createFrom(source: any = {}) {
	        return new FieldEntry(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.field = source["field"];
	        this.value = source["value"];
	    }
	}
	export class FileItem {
	    name: string;
	    size: number;
	    modTime: string;
	    mode: string;
	    isDir: boolean;
	    isHidden: boolean;
	    owner: string;
	    group: string;
	
	    static createFrom(source: any = {}) {
	        return new FileItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.size = source["size"];
	        this.modTime = source["modTime"];
	        this.mode = source["mode"];
	        this.isDir = source["isDir"];
	        this.isHidden = source["isHidden"];
	        this.owner = source["owner"];
	        this.group = source["group"];
	    }
	}
	export class FileListResult {
	    files: FileItem[];
	    dir: string;
	
	    static createFrom(source: any = {}) {
	        return new FileListResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.files = this.convertValues(source["files"], FileItem);
	        this.dir = source["dir"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class Identity {
	    id: string;
	    name: string;
	    username: string;
	    authType: string;
	    password?: string;
	    keyPath?: string;
	
	    static createFrom(source: any = {}) {
	        return new Identity(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.username = source["username"];
	        this.authType = source["authType"];
	        this.password = source["password"];
	        this.keyPath = source["keyPath"];
	    }
	}
	export class IdentityStoreData {
	    identities: Identity[];
	
	    static createFrom(source: any = {}) {
	        return new IdentityStoreData(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.identities = this.convertValues(source["identities"], Identity);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class MongoIndexInfo {
	    name: string;
	    keys: string[];
	    type: string;
	    unique: boolean;
	
	    static createFrom(source: any = {}) {
	        return new MongoIndexInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.keys = source["keys"];
	        this.type = source["type"];
	        this.unique = source["unique"];
	    }
	}
	export class MongoQueryResult {
	    documents: string[];
	    total: number;
	    skip: number;
	    limit: number;
	
	    static createFrom(source: any = {}) {
	        return new MongoQueryResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.documents = source["documents"];
	        this.total = source["total"];
	        this.skip = source["skip"];
	        this.limit = source["limit"];
	    }
	}
	export class NetCardInfo {
	    name: string;
	    state: string;
	    mac: string;
	    speed: string;
	    type: string;
	    bondMaster: string;
	    bondSlaves: string[];
	    ipAddrs: string[];
	
	    static createFrom(source: any = {}) {
	        return new NetCardInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.state = source["state"];
	        this.mac = source["mac"];
	        this.speed = source["speed"];
	        this.type = source["type"];
	        this.bondMaster = source["bondMaster"];
	        this.bondSlaves = source["bondSlaves"];
	        this.ipAddrs = source["ipAddrs"];
	    }
	}
	export class PortInfo {
	    protocol: string;
	    localAddr: string;
	    state: string;
	    process: string;
	
	    static createFrom(source: any = {}) {
	        return new PortInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.protocol = source["protocol"];
	        this.localAddr = source["localAddr"];
	        this.state = source["state"];
	        this.process = source["process"];
	    }
	}
	
	export class Proxy {
	    id: string;
	    name: string;
	    kind: string;
	    host: string;
	    port: number;
	    user?: string;
	    pass?: string;
	
	    static createFrom(source: any = {}) {
	        return new Proxy(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.kind = source["kind"];
	        this.host = source["host"];
	        this.port = source["port"];
	        this.user = source["user"];
	        this.pass = source["pass"];
	    }
	}
	export class ProxyStoreData {
	    proxies: Proxy[];
	
	    static createFrom(source: any = {}) {
	        return new ProxyStoreData(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.proxies = this.convertValues(source["proxies"], Proxy);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class RedisKeyInfo {
	    name: string;
	    type: string;
	    ttl: number;
	
	    static createFrom(source: any = {}) {
	        return new RedisKeyInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.type = source["type"];
	        this.ttl = source["ttl"];
	    }
	}
	export class ScanResult {
	    keys: RedisKeyInfo[];
	    cursor: number;
	    scanCount: number;
	
	    static createFrom(source: any = {}) {
	        return new ScanResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.keys = this.convertValues(source["keys"], RedisKeyInfo);
	        this.cursor = source["cursor"];
	        this.scanCount = source["scanCount"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class ScoredMember {
	    score: number;
	    member: string;
	
	    static createFrom(source: any = {}) {
	        return new ScoredMember(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.score = source["score"];
	        this.member = source["member"];
	    }
	}
	export class SessionInfo {
	    id: string;
	    type: string;
	    title: string;
	    status: string;
	
	    static createFrom(source: any = {}) {
	        return new SessionInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.type = source["type"];
	        this.title = source["title"];
	        this.status = source["status"];
	    }
	}
	export class SocksProxy {
	    kind: string;
	    host: string;
	    port: number;
	    user?: string;
	    pass?: string;
	
	    static createFrom(source: any = {}) {
	        return new SocksProxy(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.kind = source["kind"];
	        this.host = source["host"];
	        this.port = source["port"];
	        this.user = source["user"];
	        this.pass = source["pass"];
	    }
	}
	export class Tunnel {
	    id: string;
	    name: string;
	    mode: string;
	    sshConnId: string;
	    listenHost?: string;
	    listenPort: number;
	    targetHost?: string;
	    targetPort?: number;
	    upstream?: SocksProxy;
	    autoStart?: boolean;
	    groupId?: string;
	    sortOrder?: number;
	
	    static createFrom(source: any = {}) {
	        return new Tunnel(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.mode = source["mode"];
	        this.sshConnId = source["sshConnId"];
	        this.listenHost = source["listenHost"];
	        this.listenPort = source["listenPort"];
	        this.targetHost = source["targetHost"];
	        this.targetPort = source["targetPort"];
	        this.upstream = this.convertValues(source["upstream"], SocksProxy);
	        this.autoStart = source["autoStart"];
	        this.groupId = source["groupId"];
	        this.sortOrder = source["sortOrder"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class TunnelGroup {
	    id: string;
	    name: string;
	    sortOrder?: number;
	
	    static createFrom(source: any = {}) {
	        return new TunnelGroup(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.sortOrder = source["sortOrder"];
	    }
	}
	export class TunnelState {
	    id: string;
	    status: string;
	    localPort?: number;
	    error?: string;
	
	    static createFrom(source: any = {}) {
	        return new TunnelState(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.status = source["status"];
	        this.localPort = source["localPort"];
	        this.error = source["error"];
	    }
	}
	export class TunnelStoreData {
	    version: number;
	    groups: TunnelGroup[];
	    tunnels: Tunnel[];
	
	    static createFrom(source: any = {}) {
	        return new TunnelStoreData(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.version = source["version"];
	        this.groups = this.convertValues(source["groups"], TunnelGroup);
	        this.tunnels = this.convertValues(source["tunnels"], Tunnel);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

export namespace store {
	
	export class AIConfig {
	    apiKey: string;
	    baseURL: string;
	    model: string;
	
	    static createFrom(source: any = {}) {
	        return new AIConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.apiKey = source["apiKey"];
	        this.baseURL = source["baseURL"];
	        this.model = source["model"];
	    }
	}
	export class AIMessageEntry {
	    id: string;
	    role: string;
	    content: string;
	    tool_call_id?: string;
	    tool_calls?: any[];
	    pendingTools?: any[];
	    _rawApiMsg?: string;
	
	    static createFrom(source: any = {}) {
	        return new AIMessageEntry(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.role = source["role"];
	        this.content = source["content"];
	        this.tool_call_id = source["tool_call_id"];
	        this.tool_calls = source["tool_calls"];
	        this.pendingTools = source["pendingTools"];
	        this._rawApiMsg = source["_rawApiMsg"];
	    }
	}
	export class AIModelConfig {
	    id: string;
	    name: string;
	    apiKey: string;
	    baseURL: string;
	    model: string;
	    protocol: string;
	
	    static createFrom(source: any = {}) {
	        return new AIModelConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.apiKey = source["apiKey"];
	        this.baseURL = source["baseURL"];
	        this.model = source["model"];
	        this.protocol = source["protocol"];
	    }
	}
	export class AISessionEntry {
	    id: string;
	    name: string;
	    createdAt: number;
	    updatedAt: number;
	    messages: AIMessageEntry[];
	
	    static createFrom(source: any = {}) {
	        return new AISessionEntry(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.createdAt = source["createdAt"];
	        this.updatedAt = source["updatedAt"];
	        this.messages = this.convertValues(source["messages"], AIMessageEntry);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class AISessionData {
	    sessions: AISessionEntry[];
	    currentSessionId: string;
	
	    static createFrom(source: any = {}) {
	        return new AISessionData(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.sessions = this.convertValues(source["sessions"], AISessionEntry);
	        this.currentSessionId = source["currentSessionId"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	
	export class AISettings {
	    maxTurns?: number;
	    fontSize?: number;
	    models: AIModelConfig[];
	    activeModelId: string;
	
	    static createFrom(source: any = {}) {
	        return new AISettings(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.maxTurns = source["maxTurns"];
	        this.fontSize = source["fontSize"];
	        this.models = this.convertValues(source["models"], AIModelConfig);
	        this.activeModelId = source["activeModelId"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class TerminalThemeColors {
	    background: string;
	    foreground: string;
	    cursor: string;
	    selection: string;
	    black: string;
	    red: string;
	    green: string;
	    yellow: string;
	    blue: string;
	    magenta: string;
	    cyan: string;
	    white: string;
	    brightBlack: string;
	    brightRed: string;
	    brightGreen: string;
	    brightYellow: string;
	    brightBlue: string;
	    brightMagenta: string;
	    brightCyan: string;
	    brightWhite: string;
	
	    static createFrom(source: any = {}) {
	        return new TerminalThemeColors(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.background = source["background"];
	        this.foreground = source["foreground"];
	        this.cursor = source["cursor"];
	        this.selection = source["selection"];
	        this.black = source["black"];
	        this.red = source["red"];
	        this.green = source["green"];
	        this.yellow = source["yellow"];
	        this.blue = source["blue"];
	        this.magenta = source["magenta"];
	        this.cyan = source["cyan"];
	        this.white = source["white"];
	        this.brightBlack = source["brightBlack"];
	        this.brightRed = source["brightRed"];
	        this.brightGreen = source["brightGreen"];
	        this.brightYellow = source["brightYellow"];
	        this.brightBlue = source["brightBlue"];
	        this.brightMagenta = source["brightMagenta"];
	        this.brightCyan = source["brightCyan"];
	        this.brightWhite = source["brightWhite"];
	    }
	}
	export class CustomTerminalTheme {
	    id: string;
	    name: string;
	    type: string;
	    colors: TerminalThemeColors;
	
	    static createFrom(source: any = {}) {
	        return new CustomTerminalTheme(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.type = source["type"];
	        this.colors = this.convertValues(source["colors"], TerminalThemeColors);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class SFTPBookmarks {
	    localPaths: string[];
	    remotePaths: string[];
	
	    static createFrom(source: any = {}) {
	        return new SFTPBookmarks(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.localPaths = source["localPaths"];
	        this.remotePaths = source["remotePaths"];
	    }
	}
	export class KeyBinding {
	    ctrl: boolean;
	    meta: boolean;
	    shift: boolean;
	    alt: boolean;
	    key: string;
	
	    static createFrom(source: any = {}) {
	        return new KeyBinding(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.ctrl = source["ctrl"];
	        this.meta = source["meta"];
	        this.shift = source["shift"];
	        this.alt = source["alt"];
	        this.key = source["key"];
	    }
	}
	export class TerminalSettings {
	    theme: string;
	    fontFamily: string;
	    fontSize: number;
	    selectionAction: string;
	    rightClickAction: string;
	    maxHistoryLines: number;
	    smartCompletion?: boolean;
	    aiTranscription?: boolean;
	    highlightEnabled?: boolean;
	    cursorBlink?: boolean;
	    sessionLogDir?: string;
	    sessionLogFilename?: string;
	    wordSeparator?: string;
	
	    static createFrom(source: any = {}) {
	        return new TerminalSettings(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.theme = source["theme"];
	        this.fontFamily = source["fontFamily"];
	        this.fontSize = source["fontSize"];
	        this.selectionAction = source["selectionAction"];
	        this.rightClickAction = source["rightClickAction"];
	        this.maxHistoryLines = source["maxHistoryLines"];
	        this.smartCompletion = source["smartCompletion"];
	        this.aiTranscription = source["aiTranscription"];
	        this.highlightEnabled = source["highlightEnabled"];
	        this.cursorBlink = source["cursorBlink"];
	        this.sessionLogDir = source["sessionLogDir"];
	        this.sessionLogFilename = source["sessionLogFilename"];
	        this.wordSeparator = source["wordSeparator"];
	    }
	}
	export class AppSettings {
	    theme: string;
	    language: string;
	    terminal: TerminalSettings;
	    ai: AISettings;
	    keyboard: Record<string, KeyBinding>;
	    autoCheckUpdate?: boolean;
	    closeTabPrompt?: boolean;
	    closeAppPrompt?: boolean;
	    sftpBookmarks: SFTPBookmarks;
	    customTerminalThemes: CustomTerminalTheme[];
	    defaultLocalShell: string;
	    tabCloseButton: string;
	
	    static createFrom(source: any = {}) {
	        return new AppSettings(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.theme = source["theme"];
	        this.language = source["language"];
	        this.terminal = this.convertValues(source["terminal"], TerminalSettings);
	        this.ai = this.convertValues(source["ai"], AISettings);
	        this.keyboard = this.convertValues(source["keyboard"], KeyBinding, true);
	        this.autoCheckUpdate = source["autoCheckUpdate"];
	        this.closeTabPrompt = source["closeTabPrompt"];
	        this.closeAppPrompt = source["closeAppPrompt"];
	        this.sftpBookmarks = this.convertValues(source["sftpBookmarks"], SFTPBookmarks);
	        this.customTerminalThemes = this.convertValues(source["customTerminalThemes"], CustomTerminalTheme);
	        this.defaultLocalShell = source["defaultLocalShell"];
	        this.tabCloseButton = source["tabCloseButton"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class CommandMeta {
	    name: string;
	    description: string;
	    argumentHint: string;
	    origin: string;
	    locked: boolean;
	    enabled: boolean;
	    sortOrder: number;
	    path: string;
	    createdAt: string;
	    version: number;
	
	    static createFrom(source: any = {}) {
	        return new CommandMeta(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.description = source["description"];
	        this.argumentHint = source["argumentHint"];
	        this.origin = source["origin"];
	        this.locked = source["locked"];
	        this.enabled = source["enabled"];
	        this.sortOrder = source["sortOrder"];
	        this.path = source["path"];
	        this.createdAt = source["createdAt"];
	        this.version = source["version"];
	    }
	}
	
	export class HistoryEntry {
	    id: string;
	    command: string;
	
	    static createFrom(source: any = {}) {
	        return new HistoryEntry(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.command = source["command"];
	    }
	}
	
	export class LocalState {
	    sidebarVisible: boolean;
	    aiSidebarVisible: boolean;
	    collapsedGroupIds: string[];
	    windowX: number;
	    windowY: number;
	    windowWidth: number;
	    windowHeight: number;
	    windowMaximised: boolean;
	    backgroundEnabled: boolean;
	    backgroundImage: string;
	    backgroundOpacity: number;
	    backgroundBlur: number;
	    backgroundFit: string;
	    systemTitleBar: boolean;
	
	    static createFrom(source: any = {}) {
	        return new LocalState(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.sidebarVisible = source["sidebarVisible"];
	        this.aiSidebarVisible = source["aiSidebarVisible"];
	        this.collapsedGroupIds = source["collapsedGroupIds"];
	        this.windowX = source["windowX"];
	        this.windowY = source["windowY"];
	        this.windowWidth = source["windowWidth"];
	        this.windowHeight = source["windowHeight"];
	        this.windowMaximised = source["windowMaximised"];
	        this.backgroundEnabled = source["backgroundEnabled"];
	        this.backgroundImage = source["backgroundImage"];
	        this.backgroundOpacity = source["backgroundOpacity"];
	        this.backgroundBlur = source["backgroundBlur"];
	        this.backgroundFit = source["backgroundFit"];
	        this.systemTitleBar = source["systemTitleBar"];
	    }
	}
	export class QuickCommand {
	    id: string;
	    name?: string;
	    remark?: string;
	    command: string;
	    groupId?: string;
	    sortOrder: number;
	
	    static createFrom(source: any = {}) {
	        return new QuickCommand(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.remark = source["remark"];
	        this.command = source["command"];
	        this.groupId = source["groupId"];
	        this.sortOrder = source["sortOrder"];
	    }
	}
	export class QuickCommandGroup {
	    id: string;
	    name: string;
	    sortOrder: number;
	
	    static createFrom(source: any = {}) {
	        return new QuickCommandGroup(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.sortOrder = source["sortOrder"];
	    }
	}
	export class QuickCommandData {
	    version: number;
	    groups: QuickCommandGroup[];
	    commands: QuickCommand[];
	
	    static createFrom(source: any = {}) {
	        return new QuickCommandData(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.version = source["version"];
	        this.groups = this.convertValues(source["groups"], QuickCommandGroup);
	        this.commands = this.convertValues(source["commands"], QuickCommand);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	
	
	export class SkillFileList {
	    references: string[];
	    scripts: string[];
	
	    static createFrom(source: any = {}) {
	        return new SkillFileList(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.references = source["references"];
	        this.scripts = source["scripts"];
	    }
	}
	export class SkillMeta {
	    name: string;
	    description: string;
	    isSystem: boolean;
	    origin: string;
	    locked: boolean;
	    enabled: boolean;
	    sortOrder: number;
	    dir: string;
	    path: string;
	    hasReferences: boolean;
	    scriptCount: number;
	    modelInvocable: boolean;
	    createdModel: string;
	    createdAt: string;
	    version: number;
	
	    static createFrom(source: any = {}) {
	        return new SkillMeta(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.name = source["name"];
	        this.description = source["description"];
	        this.isSystem = source["isSystem"];
	        this.origin = source["origin"];
	        this.locked = source["locked"];
	        this.enabled = source["enabled"];
	        this.sortOrder = source["sortOrder"];
	        this.dir = source["dir"];
	        this.path = source["path"];
	        this.hasReferences = source["hasReferences"];
	        this.scriptCount = source["scriptCount"];
	        this.modelInvocable = source["modelInvocable"];
	        this.createdModel = source["createdModel"];
	        this.createdAt = source["createdAt"];
	        this.version = source["version"];
	    }
	}
	

}

export namespace sync {
	
	export class ConflictInfo {
	    // Go type: time
	    localTime: any;
	    // Go type: time
	    remoteTime: any;
	
	    static createFrom(source: any = {}) {
	        return new ConflictInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.localTime = this.convertValues(source["localTime"], null);
	        this.remoteTime = this.convertValues(source["remoteTime"], null);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class SyncConfig {
	    repoUrl: string;
	    branch: string;
	    username: string;
	    autoSync: boolean;
	    // Go type: time
	    lastSyncAt: any;
	    lastSyncStatus: string;
	    lastSyncError: string;
	
	    static createFrom(source: any = {}) {
	        return new SyncConfig(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.repoUrl = source["repoUrl"];
	        this.branch = source["branch"];
	        this.username = source["username"];
	        this.autoSync = source["autoSync"];
	        this.lastSyncAt = this.convertValues(source["lastSyncAt"], null);
	        this.lastSyncStatus = source["lastSyncStatus"];
	        this.lastSyncError = source["lastSyncError"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}
	export class SyncResult {
	    direction: number;
	    message: string;
	    conflict?: ConflictInfo;
	
	    static createFrom(source: any = {}) {
	        return new SyncResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.direction = source["direction"];
	        this.message = source["message"];
	        this.conflict = this.convertValues(source["conflict"], ConflictInfo);
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

export namespace update {
	
	export class UpdateInfo {
	    hasUpdate: boolean;
	    current: string;
	    latest: string;
	    releaseUrl: string;
	
	    static createFrom(source: any = {}) {
	        return new UpdateInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.hasUpdate = source["hasUpdate"];
	        this.current = source["current"];
	        this.latest = source["latest"];
	        this.releaseUrl = source["releaseUrl"];
	    }
	}

}

