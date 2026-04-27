export interface ApiParameter {
  name: string;
  type: string;
  optional?: boolean;
  description: string;
}

export interface ApiExample {
  title?: string;
  code: string;
  description?: string;
}

export interface ApiEntry {
  name: string;
  signature: string;
  description: string;
  parameters?: ApiParameter[];
  returns?: string;
  examples?: ApiExample[];
  notes?: string[];
}

export interface ClassMethod {
  name: string;
  signature: string;
  description: string;
  parameters?: ApiParameter[];
  returns?: string;
}

export interface ClassEntry {
  name: string;
  signature: string;
  description: string;
  properties?: { name: string; type: string; description: string }[];
  methods?: ClassMethod[];
  examples?: ApiExample[];
}

export interface ModuleEntry {
  name: string;
  description: string;
  items: string[];
}

export interface ApiConfig {
  packageName: string;
  version: string;
  description: string;
  modules: ModuleEntry[];
  functions: ApiEntry[];
  classes: ClassEntry[];
}