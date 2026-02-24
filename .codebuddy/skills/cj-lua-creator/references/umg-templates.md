
# UMG模板

## 组件清单
### Button             - 按钮组件
### TextBlock          - 文本框控件
### RichTextBlock      - 富文本框控件
---

## ⚠️ 关键注意事项
### 🔴 必须遵守（违反将导致代码不合规）
1. **在定义表名的代码里创建的自身变量默认赋值必须为nil，禁止赋其他值**
2. **在定义表名的代码里创建的自身变量使用前必须严格判空**
3. **函数内代码如果使用到了uiObj，要求先判断uiObj变量是否存在，如果不存在打印Error日志**
4. **所有函数内代码在使用控件属性前，都要判空，判空方法如下，以Button为例**：
```lua
    if self.uiObj and CheckObjectContainsField(self.uiObj, "Button_Cancel") then
        self.uiObj.Button_Cancel:SetVisibility(ESlateVisibility.Visible);
    end
```
5. **如果用户没有明确指令，禁止加入LogD日志**
---

## ⚠️ 非Button控件注意事项
### 🔴 只有不是Botton的控件才需要遵守，Button控件严禁遵守
1. **控件的显示如无特殊要求默认直接使用ESlateVisibility.SelfHitTestInvisible，示例如下**：
```lua
-- ✅ 正确：ESlateVisibility.Collapsed
    self.uiObj.Button_CloseUI:SetVisibility(ESlateVisibility.SelfHitTestInvisible);
-- ❌ 错误：使用内联样式
    self.uiObj.Button_CloseUI:SetVisibility(UE4.ESlateVisibility.SelfHitTestInvisible);
```
2. **控件的隐藏如无特殊要求默认直接使用ESlateVisibility.Collapsed，示例如下**：
```lua
-- ✅ 正确：ESlateVisibility.Collapsed
    self.uiObj.Button_CloseUI:SetVisibility(ESlateVisibility.Collapsed);
-- ❌ 错误：使用内联样式
    self.uiObj.Button_CloseUI:SetVisibility(UE4.ESlateVisibility.Collapsed);
```
3. **对于非Button类控件，不需要绑定OnClick事件**
---

## UI框架模板实例
### 文件头
```lua
if ... then _G[...] = nil end;local _ENV = LobbyENV or _ENV;
```
### 定义一个表名
```lua
LuaTableNameUI = {
    uiObj = nil,
}
```
### 注册UI
> **蓝图路径规范（🔴 必须遵守）**：BluePrintFilePath是蓝图资源路径。不包含WidgetBlueprint的字符串
```lua
--注册UI
function LuaFileName_RegisterUI()
    LuaClassObj.SubUIWidgetList(LuaFileName,
        {
            {Path="/Game/BluePrintFilePath_C", Container="Default", ZOrder=BP_ENUM_UI_SELECTMAP_ZORDER},
        },
        {"Lobby"},
        false,
        false,
        true,
        false
    );
end
--UI被创建
function LuaFileName_OnWidgetListCreated()
    -- 重置 UMG 缓存，及其相关初始化操作(事件绑定、显示初始化)
    LuaTableNameUI.uiObj = GetUIObject(LuaFileName, "BluePrintName_C");
end

--UI被销毁
function LuaFileName_OnWidgetListDestroyed(widget_cnt)
    -- 重置UI相关状态
    LuaTableNameUI:ReleaseUI();
    LuaTableNameUI.uiObj = nil;
end

--UI显示后执行
function LuaFileName_OnAfterShow(widget_name)
end

--UI隐藏否执行
function LuaFileName_OnAfterHide(widget_name)
end

--释放UI相关数据
function LuaTableNameUI:ReleaseUI()
    self:BindEvent(false);
end

--判断UI是否显示
function LuaTableNameUI:IsShow()
    return self.uiObj ~= nil and self.uiObj:Visible();
end

--绑定UI内控件的事件
function LuaTableNameUI:BindEvent(isbind)
    if not self.uiObj then
        return;
    end
    if(isbind)then
        
    else

    end
end

--显示UI
--此函数可以传入参数，控制内部组件的变量都由函数参数传入而不是在表名中创建
--此函数的生成的代码，如果示例中存在，那么其中的顺序也禁止调整，如果不存在，将其生成到函数最后
--如果有参数，可以按照如下方法定义函数，参数数量根据玩家描述添加
function LuaTableNameUI:ShowUI(title, content, okcallback, cancelcallback)
--如果没有参数，可以按照如下方法定义函数
function LuaTableNameUI:ShowUI()
-------------------------------------------------------------------------------

--如果有okCallback或者cancelCallback等回调参数。需要加入如下代码。如果需要生成，必须在最开头
    if not okCallback or type(okCallback)~= "function" then
        logE("ERROR!!!----Test MessageBox UIBPUI:ShowUI----okcallback = nil or not a function");
        return;
    end
    if not cancelCallback or type(cancelCallback)~= "function" then
        logE("ERROR!!!----Test MessageBox UIBPUI:ShowUI----cancelcallback = nil or not a function")
        return;
    end
-----------------------------------------------------------------------------------

--这行代码必须存在，必须放到callback判断后面，uiObj判断前面
    LuaClassObj.HandleDynamicCreation(LuaFileName);
-------------------------------------------------
    if self.uiObj == nil then
        logE("ERROR!!!----LuaTableNameUI:ShowUI----uiObj = nil");
        return;
    end
    if self.uiObj:Visible() then
        logE("ERROR!!!----LuaTableNameUI:ShowUI----Visible = true");
        return;
    end

--如果有参数，必须按照如下方法初始化
    self.titleText = title or "";
    self.contentText =content or "";
    self.okCallback = okCallback;
    self.cancelCallback= cancelCallback;
--------------------------------------------------

    GlobalData.PushPanel(LuaFileName,"","LuaTableNameUI");
    self.uiObj:Show();
    self:BindEvent(true);
--此处添加用户提问中，所有带有**默认**的操作
----------------------------------------
    self:RefreshUI();
end

--刷新UI显示内容
function LuaTableNameUI:RefreshUI()
    if not self.uiObj then
        logE("ERROR!!!----LuaTableNameUI:RefreshUI----uiObj = nil");
        return;
    end
    
end

--隐藏UI
function LuaTableNameUI:HideUI()
    if not self.uiObj then
        return;
    end
    self.uiObj:Hide();
    self:ReleaseUI();
end

GameFrontendHUD:CreateLogicManager("LuaFileName");
```
---

## UI控件模板

### 1 Button按钮控件
    
#### 1.1 需要根据变量名生成对应的控件代码
```lua
    function LuaTableNameUI:BindEvent(isbind)
        if not self.uiObj then
            return;
        end
        if(isbind)then
            self.uiObj.ButtonName.OnClicked:Add(self.OnClickButtonNameBtn,self);
        
        else
            self.uiObj.ButtonName.OnClicked:RemoveAll();

        end
    end

    --按钮点击方法
	function LuaTableNameUI:OnClickButtonNameBtn()
    	
	end
```

#### 1.2 如果按钮的变量名包含Close或者Hide等字样，需要生成如下样式代码
```lua
function LuaTableNameUI:BindEvent(isbind)
        if not self.uiObj then
            return;
        end
        if(isbind)then
            self.uiObj.Button_Close.OnClicked:Add(self.OnClickCloseBtn,self);
        
        else
            self.uiObj.Button_Close.OnClicked:RemoveAll();

        end
    end
	function LuaTableNameUI:OnClickCloseBtn()
		LuaTableNameUI:HideUI();
	end

```

#### 1.3 ⚠️ 关键注意
1. **🔴 参数是callback的function时，必须判断参数的类型是否是function，如果不是要打印Error日志**
2. **🔴 控件的隐藏一定要直接使用ESlateVisibility.Collapsed，不是UE4.ESlateVisibility.Collapsed 示例如下**
```lua
-- ✅ 正确：ESlateVisibility.Collapsed
    self.uiObj.Button_CloseUI:SetVisibility(ESlateVisibility.Collapsed);
-- ❌ 错误：使用内联样式
    self.uiObj.Button_CloseUI:SetVisibility(UE4.ESlateVisibility.Collapsed);
```
3. **🔴 控件的隐藏一定要直接使用ESlateVisibility.Visible，不是UE4.ESlateVisibility.Visible 示例如下**：
```lua
-- ✅ 正确：ESlateVisibility.Collapsed
    self.uiObj.Button_CloseUI:SetVisibility(ESlateVisibility.Visible);
-- ❌ 错误：使用内联样式
    self.uiObj.Button_CloseUI:SetVisibility(UE4.ESlateVisibility.Visible);
```
4. **callback的调用必须要使用xpcall来调用，错误处理方法必须要使用LuaXPCallMsgHandler这个方法 示例如下**：
```lua
	xpcall(callbackfunction, LuaXPCallMsgHandler);
```

#### 1.4 隐藏Button按钮方法示例
```lua
function LuaTableNameUI:HidexxxBtn()
    if not self.uiObj then
        return;
    end
    if self.uiObj and CheckObjectContainsField(self.uiObj, "Button_CloseUI") then
        self.uiObj.Button_CloseUI:SetVisibility(ESlateVisibility.Collapsed);
    end
end
```
### 1.5 显示Button按钮方法示例
```lua
function LuaTableNameUI:ShowxxxBtn()
    if not self.uiObj then
        return;
    end
    if self.uiObj and CheckObjectContainsField(self.uiObj, "Button_CloseUI") then
        self.uiObj.Button_CloseUI:SetVisibility(ESlateVisibility.Visible);
    end
end
```

### 2 TextBlock文本框控件

#### 2.1 Text的赋值方法
> **如果用户有**
```lua
	function LuaTableNameUI:RefreshUI()
		self.uiObj.TextBlock_Search:SetText("");
	end
```

#### 2.2 Text赋值函数
> **⚠️注意事项一**：SetText中如果传入变量，传入之前**必须**判空,**必须**添加tostring()方法
> **⚠️注意事项二**：在设置文本的函数中，如果变量为nil或者空字符串，直接返回，以设置Title为例，示例代码如下：
```lua
	function LuaTableNameUI:SetTitle(title)
		if self.titleText == nil or self.titleText == "" then
            return;
        end

        self.titleText = title;
	    if not self.uiObj then
            return;
        end
        if CheckObjectContainsField(self.uiObj, "TextBlock_Title") then
            self.uiObj.TextBlock_Title:SetText(tostring(self.titleText));
        end
	end
```

### 3 RichTextBlock富文本框控件

#### 3.1 需要在RefreshUI方法中生成对应赋值代码
```lua
	function LuaTableNameUI:RefreshUI()
		
		self.uiObj.RichTextBlock_Content:SetText("");
	end
```

#### 3.2 Text赋值函数
> **⚠️注意事项**：SetText中如果传入变量，传入之前**必须**判空,**必须**添加tostring()方法
> **⚠️注意事项二**：在设置文本的函数中，如果变量为nil或者空字符串，直接返回，以设置Title为例，示例代码如下：
```lua
	function LuaTableNameUI:SetTitle(title)
		if self.titleText == nil or self.titleText == "" then
            return;
        end
        
        self.titleText = title;
	    if not self.uiObj then
            return;
        end
        if CheckObjectContainsField(self.uiObj, "TextBlock_Title") then
            self.uiObj.TextBlock_Title:SetText(tostring(self.titleText));
        end
	end
```
---