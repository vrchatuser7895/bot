local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local TextService = game:GetService("TextService")
local HttpService = game:GetService("HttpService")

-- Executor-safe request utility
local requestFunc = syn and syn.request or request or fluxus and fluxus.request or http and http.request or http_request or (crypt and crypt.request)
if not requestFunc then
  error("[Xnoctis] Executor request function not found!")
end

local JSON_URL = "https://raw.githubusercontent.com/vrchatuser7895/bot/main/Tags.json"
local BOOSTER_URL = "https://raw.githubusercontent.com/vrchatuser7895/bot/main/booster.json"
local SUPABASE_URL = "https://mrrivrbhfkpiygoamnzb.supabase.co"
local SUPABASE_KEY = "sb_publishable_dVYRE5xvmiK1vBJL_rdLAA_RYHDR50R"

local CONFIG = {
  TAG_SIZE = UDim2.new(0, 180, 0, 50),
  TAG_OFFSET = Vector3.new(0, 2.0, 0),
  MAX_DISTANCE = math.huge, -- Show at any distance
  DISTANCE_THRESHOLD = 50, -- Threshold to minimize/maximize tag
  HYSTERESIS = 5,
  CORNER_RADIUS = UDim.new(0, 14),
  TELEPORT_DISTANCE = 5,
  TELEPORT_HEIGHT = 0.5,
  REFRESH_INTERVAL = 5, -- Data fetch interval
}

-- Custom styling definitions
local RankData = {
  ["Xnoctis"] = {
    primary = Color3.fromRGB(0, 0, 0),
    accent = ColorSequence.new{
      ColorSequenceKeypoint.new(0, Color3.fromRGB(173, 216, 230)),
      ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 255, 255))
    },
    image = "https://www.roblox.com/asset/?id=95873225919618",
    tag = "XNOCTIS"
  },
  ["BOOSTER"] = {
    primaryColor = {10, 5, 12},
    textColor = {255, 115, 250},
    borderColor = {255, 115, 250},
    tag = "BOOSTER",
    image = "https://www.roblox.com/asset/?id=117161675744244"
  },
  ["SUPPORT"] = {
    primaryColor = {5, 12, 5},
    textColor = {38, 255, 0},
    borderColor = {38, 255, 0},
    tag = "SUPPORT",
    image = "https://www.roblox.com/asset/?id=71254901982782"
  },
  ["STAFF"] = {
    primaryColor = {10, 5, 15},
    textColor = {141, 0, 255},
    borderColor = {141, 0, 255},
    tag = "STAFF",
    image = "https://www.roblox.com/asset/?id=139278888309734"
  },
  ["HEAD STAFF"] = {
    primaryColor = {12, 5, 5},
    textColor = {255, 44, 48},
    borderColor = {255, 44, 48},
    tag = "HEAD STAFF",
    image = "https://www.roblox.com/asset/?id=98777504974830"
  },
  ["CONTENT CREATOR"] = {
    primaryColor = {15, 5, 15},
    textColor = {255, 45, 85},
    borderColor = {255, 45, 85},
    tag = "CONTENT CREATOR",
    image = "https://www.roblox.com/asset/?id=91979942653683"
  },
}

-- Database and State Cache
local activeUsers = {}
local customTags = {}
local boosterTags = {}
local charConns = {}

local serverId = game.JobId ~= "" and game.JobId or "global"
local registerName = Players.LocalPlayer.Name .. "|" .. serverId
activeUsers[Players.LocalPlayer.Name:lower()] = true

-- Utility Functions
local function fetchJson(url)
  local success, result = pcall(function()
    return requestFunc({
      Url = url .. "?nocache=" .. tostring(os.time()) .. tostring(math.random(1, 999999)),
      Method = "GET",
      Headers = {
        ["Cache-Control"] = "no-cache",
        ["Pragma"] = "no-cache"
      }
    })
  end)
  if success and result and result.Body then
    local decodeSuccess, decoded = pcall(function()
      return HttpService:JSONDecode(result.Body)
    end)
    if decodeSuccess then
      return decoded
    end
  end
  return nil
end

local function toColor3(arr, default)
  if arr and type(arr) == "table" and #arr >= 3 then
    return Color3.fromRGB(arr[1], arr[2], arr[3])
  end
  return default
end

local function formatRobloxImage(assetUrl)
  if not assetUrl or assetUrl == "" or assetUrl == "none" then return "" end
  local id = string.match(assetUrl, "%d+")
  if id then
    return "https://www.roblox.com/asset/?id=" .. id
  end
  return assetUrl
end

-- Teleport Utility
local teleportDebounce = false
local function teleportToPlayer(targetPlayer)
  if teleportDebounce or targetPlayer == Players.LocalPlayer then return end
  teleportDebounce = true
  
  local char = Players.LocalPlayer.Character
  local targetChar = targetPlayer.Character
  if char and targetChar then
    local hrp = char:FindFirstChild("HumanoidRootPart")
    local targetHrp = targetChar:FindFirstChild("UpperTorso") or targetChar:FindFirstChild("HumanoidRootPart")
    if hrp and targetHrp then
      local targetCFrame = targetHrp.CFrame
      hrp.CFrame = targetCFrame - (targetCFrame.LookVector * CONFIG.TELEPORT_DISTANCE) + Vector3.new(0, CONFIG.TELEPORT_HEIGHT, 0)
      
      -- Play sound
      local sound = Instance.new("Sound")
      sound.SoundId = "rbxassetid://140492333775342"
      sound.Parent = hrp
      sound.Volume = 0.5
      sound:Play()
      game.Debris:AddItem(sound, 2)
    end
  end
  
  task.wait(0.3)
  teleportDebounce = false
end

-- UI Cleanup Helper
local function clearTag(player)
  local localPlayerGui = Players.LocalPlayer:WaitForChild("PlayerGui", 5)
  if not localPlayerGui then return end
  
  local targetName = player.Name:lower()
  
  -- Clear head BillboardGui
  if player.Character and player.Character:FindFirstChild("Head") then
    for _, child in ipairs(player.Character.Head:GetChildren()) do
      if child:IsA("BillboardGui") and child.Name == "RankTag" then
        child:Destroy()
      end
    end
  end
  
  -- Clear any matching PlayerGui BillboardGuis by attribute
  for _, gui in ipairs(localPlayerGui:GetChildren()) do
    if gui:IsA("BillboardGui") and gui.Name == "RankTag" and (gui:GetAttribute("PlayerName") == targetName or gui.Adornee == nil) then
      gui:Destroy()
    end
  end
end

-- Create Tag UI
local function createTagUI(player, rankText, configData)
  if not player.Character or not player.Character:FindFirstChild("Head") then return end
  clearTag(player)
  
  local head = player.Character.Head
  local humanoid = player.Character:FindFirstChildOfClass("Humanoid")
  if humanoid then
    humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
  end
  
  configData = configData or {}
  local tagText = configData.tag or rankText
  if rankText == "Xnoctis" or tagText:lower() == "xnoctis" then
    tagText = "XNOCTIS"
  end
  
  local primaryColor = toColor3(configData.primaryColor, Color3.fromRGB(0, 0, 0))
  local textColor = toColor3(configData.textColor, Color3.fromRGB(255, 255, 255))
  
  local hasBgImage = configData.bgImage and configData.bgImage ~= ""
  local hasImage = configData.image and configData.image ~= "" and configData.image ~= "none"
  local imageAsset = configData.image
  
  if (tagText == "XNOCTIS" or rankText == "Xnoctis") and (not imageAsset or imageAsset == "" or imageAsset == "none") then
    hasImage = true
    imageAsset = "https://www.roblox.com/asset/?id=95873225919618"
  end
  
  -- Main BillboardGui
  local tag = Instance.new("BillboardGui")
  tag.Name = "RankTag"
  tag:SetAttribute("PlayerName", player.Name:lower())
  tag.Adornee = head
  tag.Size = UDim2.new(0, 180, 0, 50)
  tag.StudsOffset = CONFIG.TAG_OFFSET
  tag.AlwaysOnTop = true
  tag.MaxDistance = CONFIG.MAX_DISTANCE
  tag.LightInfluence = 0
  tag.ResetOnSpawn = false
  tag.Active = true
  
  -- Background Card
  local container = Instance.new("ImageLabel")
  container.Name = "TagContainer"
  container.Size = UDim2.new(1, 0, 1, 0)
  if hasBgImage then
    container.Image = formatRobloxImage(configData.bgImage)
    container.BackgroundTransparency = 1
    container.ScaleType = Enum.ScaleType.Crop
  else
    container.BackgroundColor3 = primaryColor
    container.BackgroundTransparency = 0
  end
  container.BorderSizePixel = 0
  container.Parent = tag
  
  local containerCorner = Instance.new("UICorner")
  containerCorner.CornerRadius = CONFIG.CORNER_RADIUS
  containerCorner.Parent = container
  
  -- Border
  local border = Instance.new("UIStroke")
  border.Thickness = 1.5
  if tagText == "XNOCTIS" then
    border.Transparency = 1
  elseif configData.borderColor then
    border.Color = toColor3(configData.borderColor)
    border.Transparency = 0
  else
    border.Transparency = 1
  end
  border.Parent = container
  
  -- Teleport Button
  local clickButton = Instance.new("TextButton")
  clickButton.Size = UDim2.new(1, 0, 1, 0)
  clickButton.BackgroundTransparency = 1
  clickButton.Text = ""
  clickButton.ZIndex = 10
  clickButton.Parent = container
  if player ~= Players.LocalPlayer then
    clickButton.MouseButton1Click:Connect(function()
      teleportToPlayer(player)
    end)
  end
  
  -- Icon
  local emojiLabel = nil
  local iconCorner = nil
  local iconSize = 30
  if hasImage then
    emojiLabel = Instance.new("ImageLabel")
    emojiLabel.Name = "EmojiLabel"
    emojiLabel.Size = UDim2.new(0, iconSize, 0, iconSize)
    emojiLabel.Position = UDim2.new(0, 8, 0.5, -iconSize/2)
    emojiLabel.BackgroundTransparency = 1
    emojiLabel.Image = formatRobloxImage(imageAsset)
    emojiLabel.ScaleType = Enum.ScaleType.Crop
    emojiLabel.ZIndex = 5
    emojiLabel.Parent = container
    
    iconCorner = Instance.new("UICorner")
    iconCorner.CornerRadius = UDim.new(0, 7)
    iconCorner.Parent = emojiLabel
  end
  
  -- Labels Layout
  local textBlockXOffset = hasImage and 46 or 24
  
  local rankLabel = Instance.new("TextLabel")
  rankLabel.Name = "RankLabel"
  rankLabel.BackgroundTransparency = 1
  rankLabel.Text = tagText
  rankLabel.TextSize = 14
  rankLabel.Font = Enum.Font.GothamBold
  rankLabel.TextColor3 = tagText == "XNOCTIS" and Color3.fromRGB(160, 160, 160) or textColor
  rankLabel.TextXAlignment = Enum.TextXAlignment.Left
  rankLabel.Position = UDim2.new(0, textBlockXOffset, 0, 9)
  rankLabel.Size = UDim2.new(1, -textBlockXOffset - 8, 0, 16)
  rankLabel.ZIndex = 5
  rankLabel.Parent = container
  
  if configData.textGradient and type(configData.textGradient) == "table" and #configData.textGradient >= 2 then
    local startColor = toColor3(configData.textGradient[1])
    local endColor = toColor3(configData.textGradient[2])
    if startColor and endColor then
      local gradient = Instance.new("UIGradient")
      gradient.Color = ColorSequence.new{
        ColorSequenceKeypoint.new(0, startColor),
        ColorSequenceKeypoint.new(1, endColor)
      }
      gradient.Parent = rankLabel
      rankLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    end
  end
  
  local displayNameLabel = Instance.new("TextLabel")
  displayNameLabel.Name = "DisplayNameLabel"
  displayNameLabel.BackgroundTransparency = 1
  displayNameLabel.Text = "@" .. (player.DisplayName or player.Name)
  displayNameLabel.TextSize = 10
  displayNameLabel.Font = Enum.Font.GothamBold
  displayNameLabel.TextColor3 = tagText == "XNOCTIS" and Color3.fromRGB(160, 160, 160) or toColor3(configData.displayNameColor, Color3.fromRGB(160, 160, 160))
  displayNameLabel.TextXAlignment = Enum.TextXAlignment.Left
  displayNameLabel.Position = UDim2.new(0, textBlockXOffset, 0, 25)
  displayNameLabel.Size = UDim2.new(1, -textBlockXOffset - 8, 0, 16)
  displayNameLabel.ZIndex = 5
  displayNameLabel.Parent = container
  
  -- Distance-based Minimized Scaling Loop
  local isMinimized = false
  local connection
  connection = RunService.Heartbeat:Connect(function()
    if not tag or not tag.Parent or not player.Character or not player.Character:FindFirstChild("Head") then
      connection:Disconnect()
      return
    end
    
    local localChar = Players.LocalPlayer.Character
    local localHead = localChar and localChar:FindFirstChild("Head")
    if localHead then
      local distance = (head.Position - localHead.Position).Magnitude
      if distance > (CONFIG.DISTANCE_THRESHOLD + CONFIG.HYSTERESIS) and not isMinimized then
        isMinimized = true
        TweenService:Create(rankLabel, TweenInfo.new(0.2), { TextTransparency = 1 }):Play()
        TweenService:Create(displayNameLabel, TweenInfo.new(0.2), { TextTransparency = 1 }):Play()
        TweenService:Create(tag, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.new(0, 40, 0, 40), StudsOffset = Vector3.new(0, 1.0, 0) }):Play()
        TweenService:Create(containerCorner, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CornerRadius = UDim.new(0, 10) }):Play()
        
        if hasImage then
          TweenService:Create(emojiLabel, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = UDim2.new(0, 0, 0, 0), Size = UDim2.new(1, 0, 1, 0) }):Play()
          TweenService:Create(iconCorner, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CornerRadius = UDim.new(0, 10) }):Play()
          if tagText ~= "XNOCTIS" then
            TweenService:Create(container, TweenInfo.new(0.3), { BackgroundColor3 = Color3.fromRGB(0, 0, 0), BackgroundTransparency = 0, ImageTransparency = 1 }):Play()
          end
        end
      elseif distance < (CONFIG.DISTANCE_THRESHOLD - CONFIG.HYSTERESIS) and isMinimized then
        isMinimized = false
        if tagText ~= "XNOCTIS" then
          container.BackgroundColor3 = primaryColor
          container.BackgroundTransparency = hasBgImage and 1 or 0
          container.ImageTransparency = hasBgImage and 0 or 1
        end
        TweenService:Create(tag, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.new(0, 180, 0, 50), StudsOffset = CONFIG.TAG_OFFSET }):Play()
        TweenService:Create(containerCorner, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CornerRadius = CONFIG.CORNER_RADIUS }):Play()
        
        if hasImage then
          TweenService:Create(emojiLabel, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = UDim2.new(0, 8, 0.5, -iconSize/2), Size = UDim2.new(0, iconSize, 0, iconSize) }):Play()
          TweenService:Create(iconCorner, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CornerRadius = UDim.new(0, 7) }):Play()
        end
        
        task.delay(0.25, function()
          if tag and tag.Parent and not isMinimized then
            TweenService:Create(rankLabel, TweenInfo.new(0.25), { TextTransparency = 0 }):Play()
            TweenService:Create(displayNameLabel, TweenInfo.new(0.25), { TextTransparency = 0 }):Play()
          end
        end)
      end
    end
  end)
  
  tag.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

-- Resolve and Apply tag
local function applyTag(player)
  if not player or not player:IsDescendantOf(Players) then return end
  
  local nameLower = player.Name:lower()
  local isSelf = (player == Players.LocalPlayer)
  
  -- Check if they are actually using the script
  local isUsingScript = isSelf or activeUsers[nameLower]
  if not isUsingScript then
    clearTag(player)
    return
  end
  
  -- 1. Custom Tags (Tags.json)
  local customData = customTags[nameLower]
  if customData then
    createTagUI(player, "custom", customData)
    return
  end
  
  -- 2. Booster / Staff Tags (booster.json)
  local boosterRole = boosterTags[nameLower]
  if boosterRole then
    local roleData = RankData[boosterRole] or RankData[boosterRole:upper()]
    if roleData then
      createTagUI(player, "custom", roleData)
      return
    end
  end
  
  -- 3. Standard Xnoctis Script Users
  createTagUI(player, "Xnoctis", RankData["Xnoctis"])
end

-- Fetch all data from GitHub and Supabase
local function refreshData()
  -- Fetch custom tags
  local customData = fetchJson(JSON_URL)
  if customData and customData.players then
    local newTags = {}
    for user, data in pairs(customData.players) do
      newTags[user:lower()] = data
    end
    customTags = newTags
  end

  -- Fetch booster tags
  local boosterData = fetchJson(BOOSTER_URL)
  if boosterData and boosterData.players then
    local newBoosterTags = {}
    for user, role in pairs(boosterData.players) do
      newBoosterTags[user:lower()] = role
    end
    boosterTags = newBoosterTags
  end

  -- Fetch Supabase active script users
  pcall(function()
    local cacheBuster = "nocache" .. tostring(os.time()) .. tostring(math.random(1, 999999))
    local res = requestFunc({
      Url = SUPABASE_URL .. "/rest/v1/Users?select=username&username=not.eq." .. cacheBuster,
      Method = "GET",
      Headers = {
        ["apikey"] = SUPABASE_KEY,
        ["Authorization"] = "Bearer " .. SUPABASE_KEY
      }
    })
    if res and res.Body then
      local data = HttpService:JSONDecode(res.Body)
      if data then
        local newActiveUsers = {}
        newActiveUsers[Players.LocalPlayer.Name:lower()] = true
        for _, row in ipairs(data) do
          local u = row.username
          if u then
            local parts = string.split(u, "|")
            local name = parts[1]
            local jId = parts[2]
            if name and jId == serverId then
              newActiveUsers[name:lower()] = true
            end
          end
        end
        activeUsers = newActiveUsers
      end
    end
  end)

  -- Update all active players immediately
  for _, plr in ipairs(Players:GetPlayers()) do
    task.spawn(applyTag, plr)
  end
end

-- Setup player connections
local function setupPlayer(player)
  if charConns[player] then charConns[player]:Disconnect() end
  charConns[player] = player.CharacterAdded:Connect(function()
    task.wait(0.5) -- wait for head to load
    applyTag(player)
  end)
  if player.Character then
    task.spawn(applyTag, player)
  end
end

-- Initialize
task.spawn(function()
  -- Register self on Supabase
  pcall(function()
    requestFunc({
      Url = SUPABASE_URL .. "/rest/v1/Users",
      Method = "POST",
      Headers = {
        ["Content-Type"] = "application/json",
        ["apikey"] = SUPABASE_KEY,
        ["Authorization"] = "Bearer " .. SUPABASE_KEY,
        ["Prefer"] = "resolution=ignore-duplicates"
      },
      Body = HttpService:JSONEncode({ username = registerName })
    })
  end)

  refreshData()
  
  -- Setup existing players
  for _, plr in ipairs(Players:GetPlayers()) do
    setupPlayer(plr)
  end
end)

Players.PlayerAdded:Connect(function(player)
  setupPlayer(player)
  task.delay(2.5, refreshData)
end)

-- Unregister self from Supabase on leave
local function unregisterSelf()
  pcall(function()
    requestFunc({
      Url = SUPABASE_URL .. "/rest/v1/Users?username=eq." .. registerName,
      Method = "DELETE",
      Headers = {
        ["apikey"] = SUPABASE_KEY,
        ["Authorization"] = "Bearer " .. SUPABASE_KEY
      }
    })
  end)
end

Players.PlayerRemoving:Connect(function(player)
  if charConns[player] then
    charConns[player]:Disconnect()
    charConns[player] = nil
  end
  clearTag(player)
  if player == Players.LocalPlayer then
    unregisterSelf()
  end
end)

game:BindToClose(unregisterSelf)

-- Background loop: Fetch updates every 5 seconds
spawn(function()
  while task.wait(CONFIG.REFRESH_INTERVAL) do
    refreshData()
  end
end)
