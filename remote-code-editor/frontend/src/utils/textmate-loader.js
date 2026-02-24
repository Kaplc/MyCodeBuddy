import * as monaco from 'monaco-editor'

/**
 * 加载 HLSL 语法高亮（完全避免分组匹配的安全版本）
 */
export function loadHLSLTextMate() {
  // 注册语言
  monaco.languages.register({ id: 'hlsl' })
  
  // 创建 Monarch tokenizer（无分组捕获版本）
  monaco.languages.setMonarchTokensProvider('hlsl', {
    defaultToken: 'identifier',
    
    // 关键字列表
    keywords: [
      'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
      'break', 'continue', 'return', 'discard', 'struct', 'typedef',
      'const', 'static', 'extern', 'volatile', 'inline', 'noinline',
      'uniform', 'shared', 'groupshared', 'linear', 'centroid',
      'nointerpolation', 'noperspective', 'sample', 'snorm', 'unorm',
      'precise', 'row_major', 'column_major', 'cbuffer', 'tbuffer',
      'register', 'packoffset', 'technique', 'pass', 'compile',
      'vertexshader', 'pixelshader', 'geometryshader', 'hullshader',
      'domainshader', 'compute', 'in', 'out', 'inout'
    ],
    
    // 内置类型
    types: [
      'void', 'bool', 'int', 'uint', 'dword', 'half', 'float', 'double',
      'bool2', 'bool3', 'bool4', 'int2', 'int3', 'int4',
      'uint2', 'uint3', 'uint4', 'half2', 'half3', 'half4',
      'float2', 'float3', 'float4', 'double2', 'double3', 'double4',
      'float2x2', 'float2x3', 'float2x4', 'float3x2', 'float3x3', 'float3x4',
      'float4x2', 'float4x3', 'float4x4', 'vector', 'matrix',
      'Texture1D', 'Texture2D', 'Texture3D', 'TextureCube',
      'Texture1DArray', 'Texture2DArray', 'TextureCubeArray',
      'Texture2DMS', 'Texture2DMSArray',
      'RWTexture1D', 'RWTexture2D', 'RWTexture3D',
      'RWTexture1DArray', 'RWTexture2DArray',
      'SamplerState', 'SamplerComparisonState',
      'Buffer', 'RWBuffer', 'StructuredBuffer', 'RWStructuredBuffer',
      'ByteAddressBuffer', 'RWByteAddressBuffer',
      'AppendStructuredBuffer', 'ConsumeStructuredBuffer',
      'InputPatch', 'OutputPatch', 'PointStream', 'LineStream', 'TriangleStream',
      'fixed', 'fixed2', 'fixed3', 'fixed4',
      'sampler', 'sampler1D', 'sampler2D', 'sampler3D', 'samplerCUBE'
    ],
    
    // 语义关键字
    semantics: [
      'SV_Position', 'SV_ClipDistance', 'SV_CullDistance',
      'SV_RenderTargetArrayIndex', 'SV_ViewportArrayIndex',
      'SV_VertexID', 'SV_InstanceID', 'SV_PrimitiveID', 'SV_IsFrontFace',
      'SV_SampleIndex', 'SV_GSInstanceID', 'SV_OutputControlPointID',
      'SV_DomainLocation', 'SV_TessFactor', 'SV_InsideTessFactor',
      'SV_Depth', 'SV_DepthGreaterEqual', 'SV_DepthLessEqual',
      'SV_Target', 'SV_Target0', 'SV_Target1', 'SV_Target2', 'SV_Target3',
      'SV_Coverage', 'SV_DispatchThreadID', 'SV_GroupID',
      'SV_GroupIndex', 'SV_GroupThreadID',
      'POSITION', 'POSITION0', 'POSITION1',
      'NORMAL', 'NORMAL0', 'TANGENT', 'TANGENT0',
      'COLOR', 'COLOR0', 'COLOR1',
      'TEXCOORD0', 'TEXCOORD1', 'TEXCOORD2', 'TEXCOORD3',
      'TEXCOORD4', 'TEXCOORD5', 'TEXCOORD6', 'TEXCOORD7',
      'BLENDWEIGHT', 'BLENDINDICES', 'VPOS', 'VFACE', 'PSIZE', 'FOG', 'DEPTH'
    ],
    
    // 内置函数
    builtinFunctions: [
      // 数学函数
      'abs', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'clamp', 'cos', 'cosh',
      'cross', 'degrees', 'distance', 'dot', 'exp', 'exp2', 'floor', 'fmod',
      'frac', 'frexp', 'ldexp', 'length', 'lerp', 'log', 'log2', 'log10',
      'max', 'min', 'modf', 'mul', 'normalize', 'pow', 'radians', 'reflect',
      'refract', 'round', 'rsqrt', 'saturate', 'sign', 'sin', 'sincos', 'sinh',
      'smoothstep', 'sqrt', 'step', 'tan', 'tanh', 'trunc',
      
      // 向量/矩阵函数
      'all', 'any', 'determinant', 'transpose',
      
      // 纹理采样函数
      'tex2D', 'tex2Dproj', 'tex2Dlod', 'tex2Dbias', 'tex2Dgrad',
      'texCUBE', 'texCUBEproj', 'texCUBElod', 'texCUBEbias',
      'tex3D', 'tex3Dproj', 'tex3Dlod', 'tex3Dbias',
      'Sample', 'SampleLevel', 'SampleBias', 'SampleGrad', 'SampleCmp', 'SampleCmpLevelZero',
      'Load', 'GetDimensions',
      
      // Unity 特有函数
      'UnityObjectToClipPos', 'UnityObjectToWorldDir', 'UnityObjectToWorldNormal',
      'UnityWorldToObjectDir', 'UnityWorldSpaceLightDir', 'UnityWorldSpaceViewDir',
      'ObjSpaceLightDir', 'ObjSpaceViewDir', 'WorldSpaceLightDir', 'WorldSpaceViewDir',
      'UnityObjectToViewPos', 'TRANSFORM_TEX', 'UNITY_MATRIX_MVP',
      
      // 其他常用函数
      'clip', 'ddx', 'ddy', 'fwidth', 'isfinite', 'isinf', 'isnan',
      'asfloat', 'asint', 'asuint', 'f16tof32', 'f32tof16',
      'InterlockedAdd', 'InterlockedAnd', 'InterlockedCompareExchange',
      'InterlockedExchange', 'InterlockedMax', 'InterlockedMin', 'InterlockedOr', 'InterlockedXor',
      'GroupMemoryBarrier', 'GroupMemoryBarrierWithGroupSync',
      'DeviceMemoryBarrier', 'DeviceMemoryBarrierWithGroupSync',
      'AllMemoryBarrier', 'AllMemoryBarrierWithGroupSync'
    ],
    
    // 常量
    constants: ['true', 'false', 'NULL'],
    
    // 常见的自定义结构体类型名称
    customTypes: [
      'v2f', 'appdata', 'appdata_base', 'appdata_full', 'appdata_tan',
      'appdata_img', 'v2f_img', 'Varyings', 'Attributes', 'VertexInput',
      'VertexOutput', 'FragmentInput', 'SurfaceOutput', 'SurfaceOutputStandard',
      'SurfaceOutputStandardSpecular', 'Input', 'VertexData', 'InterpolatorsVertex'
    ],
    
    // 操作符
    operators: [
      '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
      '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^',
      '%', '<<', '>>', '+=', '-=', '*=', '/=', '&=', '|=', '^=',
      '%=', '<<=', '>>='
    ],
    
    // 符号
    symbols: /[=><!~?:&|+\-*\/\^%]+/,
    
    // 转义字符
    escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,
    
    // Tokenizer 规则 - 完全避免数组式的 token 定义
    tokenizer: {
      root: [
        // 空白符
        [/[ \t\r\n]+/, 'white'],
        
        // 注释
        [/\/\/.*$/, 'comment'],
        [/\/\*/, 'comment', '@comment'],
        
        // 预处理器
        [/^\s*#\s*(?:define|undef|if|ifdef|ifndef|else|elif|endif|error|pragma|include|line)\b/, 'keyword.preprocessor'],
        [/\b(?:CGPROGRAM|ENDCG|CGINCLUDE|HLSLPROGRAM|ENDHLSL|HLSLINCLUDE)\b/, 'keyword.preprocessor'],
        
        // struct 关键字 - 触发结构体名称识别
        [/\bstruct\b/, 'keyword', '@struct_name'],
        
        // 识别函数参数中的类型（Type name 或 Type name,）
        [/\b[A-Z]\w*(?=\s+[a-z_]\w*\s*[,)])/, 'type.custom'],
        
        // 识别函数返回类型（Type functionName(）
        [/\b[A-Z]\w*(?=\s+[a-z_]\w*\s*\()/, 'type.custom'],
        
        // 识别函数调用（functionName( ）- 必须在关键字检查之前
        [/[a-zA-Z_]\w*(?=\s*\()/, { 
          cases: { 
            '@keywords': 'keyword',
            '@builtinFunctions': 'function.builtin',
            '@default': 'function' 
          } 
        }],
        
        // 标识符和关键字
        [/[a-zA-Z_]\w*/, { 
          cases: { 
            '@keywords': 'keyword',
            '@types': 'type',
            '@semantics': 'semantic',
            '@constants': 'constant',
            '@builtinFunctions': 'function.builtin',
            '@customTypes': 'type.custom',
            '@default': 'identifier' 
          } 
        }],
        
        // 数字
        [/0[xX][0-9a-fA-F]+[uUlL]*/, 'number'],
        [/[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?[fFhHlL]?/, 'number'],
        [/[0-9]+[uUlL]*/, 'number'],
        
        // 字符串
        [/"(?:[^"\\]|\\.)*$/, 'string.invalid'],
        [/"/, 'string', '@string'],
        
        // 操作符和符号
        [/@symbols/, { 
          cases: { 
            '@operators': 'operator',
            '@default': 'delimiter' 
          } 
        }],
        
        // 分隔符
        [/[{}()\[\]]/, '@brackets'],
        [/[;,.]/, 'delimiter'],
      ],
      
      // 结构体名称状态 - 识别 struct 后面的名称
      struct_name: [
        [/[ \t\r\n]+/, 'white'],
        [/[a-zA-Z_]\w*/, 'type.struct', '@pop'],
        ['', '', '@pop']
      ],
      
      // 注释状态
      comment: [
        [/[^\/*]+/, 'comment'],
        [/\*\//, 'comment', '@pop'],
        [/[\/*]/, 'comment']
      ],
      
      // 字符串状态
      string: [
        [/[^\\"]+/, 'string'],
        [/@escapes/, 'string.escape'],
        [/\\./, 'string.escape.invalid'],
        [/"/, 'string', '@pop']
      ]
    }
  })
  
  // 注册自动补全提供器
  registerHLSLCompletionProvider()
  
  console.log('✅ HLSL 语法高亮已加载 (v2.6 - 新增自定义函数高亮)')
}

/**
 * 注册 HLSL 自动补全
 */
function registerHLSLCompletionProvider() {
  monaco.languages.registerCompletionItemProvider('hlsl', {
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn
      }

      const suggestions = [
        // 关键字
        ...createKeywordSuggestions(range),
        // 内置类型
        ...createTypeSuggestions(range),
        // 内置函数
        ...createFunctionSuggestions(range),
        // 语义
        ...createSemanticSuggestions(range),
        // 代码片段
        ...createSnippetSuggestions(range)
      ]

      return { suggestions }
    }
  })
}

/**
 * 创建关键字建议
 */
function createKeywordSuggestions(range) {
  const keywords = [
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default',
    'break', 'continue', 'return', 'discard', 'struct', 'typedef',
    'const', 'static', 'uniform', 'in', 'out', 'inout'
  ]
  
  return keywords.map(keyword => ({
    label: keyword,
    kind: monaco.languages.CompletionItemKind.Keyword,
    insertText: keyword,
    range: range
  }))
}

/**
 * 创建类型建议
 */
function createTypeSuggestions(range) {
  const types = [
    'void', 'bool', 'int', 'uint', 'float', 'half', 'double',
    'float2', 'float3', 'float4', 'float4x4',
    'sampler2D', 'samplerCUBE', 'Texture2D', 'SamplerState'
  ]
  
  return types.map(type => ({
    label: type,
    kind: monaco.languages.CompletionItemKind.Class,
    insertText: type,
    range: range
  }))
}

/**
 * 创建函数建议
 */
function createFunctionSuggestions(range) {
  const functions = [
    { name: 'abs', snippet: 'abs($1)', doc: '返回绝对值' },
    { name: 'normalize', snippet: 'normalize($1)', doc: '归一化向量' },
    { name: 'lerp', snippet: 'lerp($1, $2, $3)', doc: '线性插值 lerp(a, b, t)' },
    { name: 'clamp', snippet: 'clamp($1, $2, $3)', doc: '限制值范围 clamp(x, min, max)' },
    { name: 'saturate', snippet: 'saturate($1)', doc: '限制到 [0, 1] 范围' },
    { name: 'dot', snippet: 'dot($1, $2)', doc: '点积' },
    { name: 'cross', snippet: 'cross($1, $2)', doc: '叉积' },
    { name: 'mul', snippet: 'mul($1, $2)', doc: '矩阵乘法' },
    { name: 'tex2D', snippet: 'tex2D($1, $2)', doc: '2D纹理采样 tex2D(sampler, uv)' },
    { name: 'length', snippet: 'length($1)', doc: '向量长度' },
    { name: 'distance', snippet: 'distance($1, $2)', doc: '两点间距离' },
    { name: 'pow', snippet: 'pow($1, $2)', doc: '幂运算 pow(x, y)' },
    { name: 'sqrt', snippet: 'sqrt($1)', doc: '平方根' },
    { name: 'sin', snippet: 'sin($1)', doc: '正弦函数' },
    { name: 'cos', snippet: 'cos($1)', doc: '余弦函数' },
    { name: 'reflect', snippet: 'reflect($1, $2)', doc: '反射向量 reflect(I, N)' },
    { name: 'refract', snippet: 'refract($1, $2, $3)', doc: '折射向量 refract(I, N, eta)' },
    { name: 'UnityObjectToClipPos', snippet: 'UnityObjectToClipPos($1)', doc: 'Unity: 对象空间到裁剪空间' },
    { name: 'TRANSFORM_TEX', snippet: 'TRANSFORM_TEX($1, $2)', doc: 'Unity: 变换纹理坐标' },
  ]
  
  return functions.map(func => ({
    label: func.name,
    kind: monaco.languages.CompletionItemKind.Function,
    insertText: func.snippet,
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    documentation: func.doc,
    range: range
  }))
}

/**
 * 创建语义建议
 */
function createSemanticSuggestions(range) {
  const semantics = [
    { name: 'SV_Position', doc: '顶点位置（裁剪空间）' },
    { name: 'SV_Target', doc: '渲染目标输出' },
    { name: 'POSITION', doc: '顶点位置' },
    { name: 'NORMAL', doc: '法线' },
    { name: 'TEXCOORD0', doc: '纹理坐标 0' },
    { name: 'TEXCOORD1', doc: '纹理坐标 1' },
    { name: 'COLOR', doc: '顶点颜色' },
    { name: 'TANGENT', doc: '切线' },
  ]
  
  return semantics.map(semantic => ({
    label: semantic.name,
    kind: monaco.languages.CompletionItemKind.Property,
    insertText: semantic.name,
    documentation: semantic.doc,
    range: range
  }))
}

/**
 * 创建代码片段建议
 */
function createSnippetSuggestions(range) {
  return [
    {
      label: 'struct',
      kind: monaco.languages.CompletionItemKind.Snippet,
      insertText: [
        'struct ${1:StructName} {',
        '\t$0',
        '};'
      ].join('\n'),
      insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
      documentation: '创建结构体',
      range: range
    },
    {
      label: 'vertfrag',
      kind: monaco.languages.CompletionItemKind.Snippet,
      insertText: [
        'v2f vert(appdata v) {',
        '\tv2f o;',
        '\to.pos = UnityObjectToClipPos(v.vertex);',
        '\t$0',
        '\treturn o;',
        '}',
        '',
        'float4 frag(v2f i) : SV_Target {',
        '\treturn float4(1, 1, 1, 1);',
        '}'
      ].join('\n'),
      insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
      documentation: '创建顶点和片元着色器函数',
      range: range
    }
  ]
}

/**
 * 定义增强的主题
 */
export function defineEnhancedTheme() {
  monaco.editor.defineTheme('enhanced-dark-hlsl', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      // 基础令牌
      { token: 'comment', foreground: '6A9955' },
      { token: 'keyword', foreground: '569CD6' },
      { token: 'keyword.preprocessor', foreground: 'C586C0' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'string.escape', foreground: 'D7BA7D' },
      { token: 'string.invalid', foreground: 'CE9178' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'operator', foreground: 'D4D4D4' },
      { token: 'delimiter', foreground: 'D4D4D4' },
      { token: 'constant', foreground: '4FC1FF' },
      
      // HLSL 专用令牌
      { token: 'type', foreground: '4EC9B0' },           // 内置类型 - 青色
      { token: 'type.struct', foreground: 'A9B7C6' },    // struct 定义的名称 - 银白色
      { token: 'type.custom', foreground: 'A9B7C6' },    // 自定义类型使用 - 银白色
      { token: 'semantic', foreground: 'FF9500' },       // 语义 - 橙色
      { token: 'function.builtin', foreground: 'DCDCAA' }, // 内置函数 - 黄色
      { token: 'function', foreground: 'DCDCAA' },       // 自定义函数 - 黄色
      { token: 'identifier', foreground: '9CDCFE' }      // 标识符 - 淡蓝色
    ],
    colors: {
      'editor.background': '#1E1E1E',
      'editor.foreground': '#D4D4D4',
      'editor.lineHighlightBackground': '#264F78',
      'editor.selectionBackground': '#264F78',
      'editor.inactiveSelectionBackground': '#264F7850',
      'editorCursor.foreground': '#AEAFAD',
      'editorLineNumber.foreground': '#858585',
      'editorLineNumber.activeForeground': '#C6C6C6'
    }
  })
  
  console.log('✅ 增强主题已定义')
}
