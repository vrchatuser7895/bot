local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")

local requestFunc = syn and syn.request or request or fluxus and fluxus.request or http and http.request or http_request or (crypt and crypt.request)
if not requestFunc then error("[Xnoctis] Executor request function not found!") end

local JSON_URL = "https://cispn.alwaysdata.net/raw/tags"
local BOOSTER_URL = "https://cispn.alwaysdata.net/raw/booster"
local SUPABASE_URL = "https://mrrivrbhfkpiygoamnzb.supabase.co"
local SUPABASE_KEY = "sb_publishable_dVYRE5xvmiK1vBJL_rdLAA_RYHDR50R"

local CONFIG = {
  TAG_SIZE = UDim2.new(0, 200, 0, 50),
  TAG_OFFSET = Vector3.new(0, 2.0, 0),
  MAX_DISTANCE = math.huge,
  DISTANCE_THRESHOLD = 50,
  HYSTERESIS = 5,
  CORNER_RADIUS = UDim.new(0, 14),
  TELEPORT_DISTANCE = 5,
  TELEPORT_HEIGHT = 0.5,
  REFRESH_INTERVAL = 5,
}

local RankData = {
  ["Xnoctis"] = {
    primary = Color3.fromRGB(0, 0, 0),
    accent = ColorSequence.new{
      ColorSequenceKeypoint.new(0, Color3.fromRGB(173, 216, 230)),
      ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 255, 255))
    },
    image = "https://www.roblox.com/asset/?id=101080719087951",
    tag = "XNOCTIS"
  },
  ["BOOSTER"] = {
    primaryColor = {10, 5, 12}, textColor = {255, 115, 250}, borderColor = {255, 115, 250},
    tag = "BOOSTER", image = "https://www.roblox.com/asset/?id=117161675744244"
  },
  ["SUPPORT"] = {
    primaryColor = {5, 12, 5}, textColor = {38, 255, 0}, borderColor = {38, 255, 0},
    tag = "SUPPORT", image = "https://www.roblox.com/asset/?id=71254901982782"
  },
  ["STAFF"] = {
    primaryColor = {10, 5, 15}, textColor = {141, 0, 255}, borderColor = {141, 0, 255},
    tag = "STAFF", image = "https://www.roblox.com/asset/?id=139278888309734"
  },
  ["HEAD STAFF"] = {
    primaryColor = {12, 5, 5}, textColor = {255, 44, 48}, borderColor = {255, 44, 48},
    tag = "HEAD STAFF", image = "https://www.roblox.com/asset/?id=98777504974830"
  },
  ["CONTENT CREATOR"] = {
    primaryColor = {15, 5, 15}, textColor = {255, 0, 0}, borderColor = {255, 0, 0},
    tag = "CONTENT CREATOR", image = "https://www.roblox.com/asset/?id=91979942653683"
  },
}

local activeUsers, customTags, boosterTags, charConns = {}, {}, {}, {}
local serverId = game.JobId ~= "" and game.JobId or "global"
local registerName = Players.LocalPlayer.Name .. "|" .. serverId
activeUsers[Players.LocalPlayer.Name:lower()] = true

local function fetchJson(url)
  local success, result = pcall(function()
    return requestFunc({
      Url = url .. "?nocache=" .. tostring(os.time()) .. tostring(math.random(1, 999999)),
      Method = "GET",
      Headers = { ["Cache-Control"] = "no-cache", ["Pragma"] = "no-cache" }
    })
  end)
  if success and result then
    local body = result.Body or result.body
    if body then
      local decodeSuccess, decoded = pcall(function() return HttpService:JSONDecode(body) end)
      if decodeSuccess then return decoded end
    end
  end
  return nil
end

local function toC3(arr, default)
  return (arr and type(arr) == "table" and #arr >= 3) and Color3.fromRGB(arr[1], arr[2], arr[3]) or default
end

local customAssetFunc = getcustomasset or getsynasset or (syn and syn.getcustomasset) or (fluxus and fluxus.getcustomasset)
local imageCache = {}
local imageDownloadsInProgress = {}

local function getUrlHash(url)
  local hash = 5381
  for i = 1, #url do
    local b = string.byte(url, i)
    hash = ((hash * 33) + b) % 2147483647
  end
  return string.format("%08x", math.abs(hash))
end

local function applyImage(imageLabel, rawUrl, callback)
  if not rawUrl or rawUrl == "" or rawUrl == "none" then
    if imageLabel then imageLabel.Image = "" end
    return ""
  end

  -- 1. Pure numeric string -> Roblox Asset ID
  if string.match(rawUrl, "^%d+$") then
    local assetStr = "rbxassetid://" .. rawUrl
    if imageLabel then imageLabel.Image = assetStr end
    if callback then callback(assetStr) end
    return assetStr
  end

  -- 2. rbxassetid://, rbxasset://, rbxthumb:// protocol
  if string.match(rawUrl, "^rbxassetid://") or string.match(rawUrl, "^rbxasset://") or string.match(rawUrl, "^rbxthumb://") then
    if imageLabel then imageLabel.Image = rawUrl end
    if callback then callback(rawUrl) end
    return rawUrl
  end

  -- 3. Roblox website asset url
  if string.find(rawUrl, "roblox%.com") or string.find(rawUrl, "rbxcdn%.com") then
    local digits = string.match(rawUrl, "%d+")
    if digits then
      local assetStr = "https://www.roblox.com/asset/?id=" .. digits
      if imageLabel then imageLabel.Image = assetStr end
      if callback then callback(assetStr) end
      return assetStr
    end
  end

  -- 4. External Web URL (e.g. Imgur, Discord, Web server, etc.)
  if string.match(rawUrl, "^https?://") then
    -- Check in-memory cache
    if imageCache[rawUrl] then
      if imageLabel then imageLabel.Image = imageCache[rawUrl] end
      if callback then callback(imageCache[rawUrl]) end
      return imageCache[rawUrl]
    end

    -- Check executor filesystem functions and custom asset function
    if customAssetFunc and writefile then
      local hash = getUrlHash(rawUrl)
      local ext = string.match(rawUrl, "%.([a-zA-Z0-9]+)%??") or "png"
      if #ext > 4 or not string.match(ext, "^%a+$") then ext = "png" end
      local folderName = "xnoctis_nametags"
      local fileName = folderName .. "/img_" .. hash .. "." .. ext

      if isfolder and makefolder and not isfolder(folderName) then
        pcall(makefolder, folderName)
      end

      if isfile and isfile(fileName) then
        local ok, asset = pcall(customAssetFunc, fileName)
        if ok and asset then
          imageCache[rawUrl] = asset
          if imageLabel then imageLabel.Image = asset end
          if callback then callback(asset) end
          return asset
        end
      end

      -- If not already downloaded, start async background download
      if not imageDownloadsInProgress[rawUrl] then
        imageDownloadsInProgress[rawUrl] = true
        task.spawn(function()
          local fetchSuccess, res = pcall(function()
            return requestFunc({
              Url = rawUrl,
              Method = "GET"
            })
          end)
          imageDownloadsInProgress[rawUrl] = nil
          if fetchSuccess and res and (res.Body or res.body) and (res.StatusCode == 200 or res.Status == 200 or not res.StatusCode) then
            local body = res.Body or res.body
            local writeOk = pcall(writefile, fileName, body)
            if writeOk then
              local assetOk, asset = pcall(customAssetFunc, fileName)
              if assetOk and asset then
                imageCache[rawUrl] = asset
                if imageLabel and imageLabel.Parent then
                  imageLabel.Image = asset
                end
                if callback then callback(asset) end
              end
            end
          end
        end)
      end
      return ""
    end

    -- Fallback if no custom asset function available
    if imageLabel then imageLabel.Image = rawUrl end
    return rawUrl
  end

  -- Fallback for any other format
  local digits = string.match(rawUrl, "%d+")
  local fallbackStr = digits and ("https://www.roblox.com/asset/?id=" .. digits) or rawUrl
  if imageLabel then imageLabel.Image = fallbackStr end
  return fallbackStr
end

local function fmtImg(u)
  return applyImage(nil, u)
end

local teleportDebounce = false
local function teleportToPlayer(targetPlayer)
  if teleportDebounce or targetPlayer == Players.LocalPlayer then return end
  teleportDebounce = true
  local char, targetChar = Players.LocalPlayer.Character, targetPlayer.Character
  if char and targetChar then
    local hrp = char:FindFirstChild("HumanoidRootPart")
    local targetHrp = targetChar:FindFirstChild("UpperTorso") or targetChar:FindFirstChild("HumanoidRootPart")
    if hrp and targetHrp then
      hrp.CFrame = targetHrp.CFrame - (targetHrp.CFrame.LookVector * CONFIG.TELEPORT_DISTANCE) + Vector3.new(0, CONFIG.TELEPORT_HEIGHT, 0)
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

local function clearTag(player)
  local pgui = Players.LocalPlayer:WaitForChild("PlayerGui", 5)
  if player.Character and player.Character:FindFirstChild("Head") then
    for _, child in ipairs(player.Character.Head:GetChildren()) do
      if child:IsA("BillboardGui") and child.Name == "RankTag" then child:Destroy() end
    end
  end
  if pgui then
    for _, gui in ipairs(pgui:GetChildren()) do
      if gui:IsA("BillboardGui") and gui.Name == "RankTag" and (gui:GetAttribute("PlayerName") == player.Name:lower() or gui.Adornee == nil) then
        gui:Destroy()
      end
    end
  end
end

local function createTagUI(player, rankText, configData)
  if not player.Character or not player.Character:FindFirstChild("Head") then return end
  clearTag(player)
  
  local head = player.Character.Head
  local humanoid = player.Character:FindFirstChildOfClass("Humanoid")
  if humanoid then humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
  
  configData = configData or {}
  local tagText = configData.tag or rankText
  if rankText == "Xnoctis" or tagText:lower() == "xnoctis" then tagText = "XNOCTIS" end
  
  local primaryColor = toC3(configData.primaryColor, Color3.fromRGB(0, 0, 0))
  local textColor = toC3(configData.textColor, Color3.fromRGB(255, 255, 255))
  local hasBgImage = configData.bgImage and configData.bgImage ~= ""
  local hasImage = configData.image and configData.image ~= "" and configData.image ~= "none"
  local imageAsset = configData.image
  
  if (tagText == "XNOCTIS" or rankText == "Xnoctis") and (not imageAsset or imageAsset == "" or imageAsset == "none") then
    hasImage, imageAsset = true, "https://www.roblox.com/asset/?id=101080719087951"
  end
  
  local initialMinimized = false
  local localChar = Players.LocalPlayer.Character
  local localHrp = localChar and localChar:FindFirstChild("HumanoidRootPart")
  if localHrp and (head.Position - localHrp.Position).Magnitude > (CONFIG.DISTANCE_THRESHOLD + CONFIG.HYSTERESIS) then
    initialMinimized = true
  end
  
  local tag = Instance.new("BillboardGui")
  tag.Name = "RankTag"
  tag:SetAttribute("PlayerName", player.Name:lower())
  tag.Adornee = head
  tag.Size = initialMinimized and UDim2.new(0, 40, 0, 40) or CONFIG.TAG_SIZE
  tag.StudsOffset = initialMinimized and Vector3.new(0, 1.0, 0) or CONFIG.TAG_OFFSET
  tag.AlwaysOnTop, tag.MaxDistance, tag.LightInfluence, tag.ResetOnSpawn, tag.Active = true, CONFIG.MAX_DISTANCE, 0, false, true
  tag.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
  
  local container = Instance.new("ImageLabel")
  container.Name = "TagContainer"
  container.Size = UDim2.new(1, 0, 1, 0)
  
  local initBgColor, initBgTrans, initImgTrans = primaryColor, 0, 0
  if initialMinimized and hasImage and tagText ~= "XNOCTIS" then
    initBgColor, initBgTrans, initImgTrans = Color3.fromRGB(0, 0, 0), 0, 1
  elseif hasBgImage then
    container.ScaleType = Enum.ScaleType.Crop
    initBgTrans = 1
    applyImage(container, configData.bgImage)
  end
  container.BackgroundColor3, container.BackgroundTransparency, container.ImageTransparency = initBgColor, initBgTrans, initImgTrans
  container.BorderSizePixel = 0
  container.Parent = tag
  
  local containerCorner = Instance.new("UICorner")
  containerCorner.CornerRadius = initialMinimized and UDim.new(0, 10) or CONFIG.CORNER_RADIUS
  containerCorner.Parent = container
  
  local border = Instance.new("UIStroke")
  border.Thickness = 1.5
  if tagText == "XNOCTIS" then border.Transparency = 1
  elseif configData.borderColor then border.Color, border.Transparency = toC3(configData.borderColor), 0
  else border.Transparency = 1 end
  border.Parent = container
  
  local clickButton = Instance.new("TextButton")
  clickButton.Size, clickButton.BackgroundTransparency, clickButton.Text, clickButton.ZIndex = UDim2.new(1, 0, 1, 0), 1, "", 10
  clickButton.Parent = container
  if player ~= Players.LocalPlayer then
    clickButton.MouseButton1Click:Connect(function() teleportToPlayer(player) end)
  end
  
  local emojiLabel, iconCorner, iconSize = nil, nil, 36
  if hasImage then
    emojiLabel = Instance.new("ImageLabel")
    emojiLabel.Name = "EmojiLabel"
    emojiLabel.Size = initialMinimized and UDim2.new(1, 0, 1, 0) or UDim2.new(0, iconSize, 0, iconSize)
    emojiLabel.Position = initialMinimized and UDim2.new(0, 0, 0, 0) or UDim2.new(0, 8, 0.5, -iconSize/2)
    emojiLabel.BackgroundTransparency, emojiLabel.ScaleType, emojiLabel.ImageColor3, emojiLabel.ZIndex = 1, Enum.ScaleType.Fit, Color3.fromRGB(255, 255, 255), 5
    applyImage(emojiLabel, imageAsset)
    emojiLabel.Parent = container
    
    iconCorner = Instance.new("UICorner")
    iconCorner.CornerRadius = initialMinimized and UDim.new(0, 10) or UDim.new(0, 7)
    iconCorner.Parent = emojiLabel
  end
  
  local textBlockXOffset = hasImage and 52 or 24
  local hideTag, hideDisplayName = configData.hideTag == true, configData.hideDisplayName == true
 
  local rankLabel = Instance.new("TextLabel")
  rankLabel.Name = "RankLabel"
  rankLabel.BackgroundTransparency, rankLabel.Text, rankLabel.TextSize, rankLabel.Font = 1, tagText, 14, Enum.Font.GothamBold
  rankLabel.TextColor3 = tagText == "XNOCTIS" and Color3.fromRGB(220, 220, 220) or textColor
  rankLabel.TextXAlignment = Enum.TextXAlignment.Left
  rankLabel.Position = UDim2.new(0, textBlockXOffset, 0, 9)
  rankLabel.Size = UDim2.new(1, -textBlockXOffset - 8, 0, 16)
  rankLabel.Visible, rankLabel.TextTransparency, rankLabel.ZIndex = not hideTag, initialMinimized and 1 or 0, 5
  rankLabel.Parent = container
  
  if configData.textGradient and type(configData.textGradient) == "table" and #configData.textGradient >= 2 then
    local startColor, endColor = toC3(configData.textGradient[1]), toC3(configData.textGradient[2])
    if startColor and endColor then
      local gradient = Instance.new("UIGradient")
      gradient.Color = ColorSequence.new{ColorSequenceKeypoint.new(0, startColor), ColorSequenceKeypoint.new(1, endColor)}
      gradient.Parent = rankLabel
      rankLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
    end
  end
  
  local displayNameLabel = Instance.new("TextLabel")
  displayNameLabel.Name = "DisplayNameLabel"
  displayNameLabel.BackgroundTransparency, displayNameLabel.Text, displayNameLabel.TextSize, displayNameLabel.Font = 1, "@" .. (player.DisplayName or player.Name), 10, Enum.Font.GothamBold
  displayNameLabel.TextColor3 = tagText == "XNOCTIS" and Color3.fromRGB(220, 220, 220) or toC3(configData.displayNameColor, Color3.fromRGB(220, 220, 220))
  displayNameLabel.TextXAlignment = Enum.TextXAlignment.Left
  displayNameLabel.Position = UDim2.new(0, textBlockXOffset, 0, 25)
  displayNameLabel.Size = UDim2.new(1, -textBlockXOffset - 8, 0, 16)
  displayNameLabel.Visible, displayNameLabel.TextTransparency, displayNameLabel.ZIndex = not hideDisplayName, initialMinimized and 1 or 0, 5
  displayNameLabel.Parent = container
  
  local function tw(obj, dur, props)
    TweenService:Create(obj, TweenInfo.new(dur, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), props):Play()
  end
  
  local isMinimized = initialMinimized
  task.spawn(function()
    while task.wait(0.1) do
      if not tag or not tag.Parent or not player.Character or not head or not head.Parent then break end
      local localChar = Players.LocalPlayer.Character
      local localHrp = localChar and localChar:FindFirstChild("HumanoidRootPart")
      if localHrp then
        local distance = (head.Position - localHrp.Position).Magnitude
        if distance > (CONFIG.DISTANCE_THRESHOLD + CONFIG.HYSTERESIS) and not isMinimized then
          isMinimized = true
          tw(rankLabel, 0.2, { TextTransparency = 1 })
          tw(displayNameLabel, 0.2, { TextTransparency = 1 })
          tw(tag, 0.5, { Size = UDim2.new(0, 40, 0, 40), StudsOffset = Vector3.new(0, 1.0, 0) })
          tw(containerCorner, 0.5, { CornerRadius = UDim.new(0, 10) })
          if hasImage then
            tw(emojiLabel, 0.5, { Position = UDim2.new(0, 0, 0, 0), Size = UDim2.new(1, 0, 1, 0) })
            tw(iconCorner, 0.5, { CornerRadius = UDim.new(0, 10) })
            if tagText ~= "XNOCTIS" then
              tw(container, 0.3, { BackgroundColor3 = Color3.fromRGB(0, 0, 0), BackgroundTransparency = 0, ImageTransparency = 1 })
            end
          end
        elseif distance < (CONFIG.DISTANCE_THRESHOLD - CONFIG.HYSTERESIS) and isMinimized then
          isMinimized = false
          if tagText ~= "XNOCTIS" then
            container.BackgroundColor3 = primaryColor
            container.BackgroundTransparency = hasBgImage and 1 or 0
            container.ImageTransparency = hasBgImage and 0 or 1
          end
          tw(tag, 0.5, { Size = CONFIG.TAG_SIZE, StudsOffset = CONFIG.TAG_OFFSET })
          tw(containerCorner, 0.5, { CornerRadius = CONFIG.CORNER_RADIUS })
          if hasImage then
            tw(emojiLabel, 0.5, { Position = UDim2.new(0, 8, 0.5, -iconSize/2), Size = UDim2.new(0, iconSize, 0, iconSize) })
            tw(iconCorner, 0.5, { CornerRadius = UDim.new(0, 7) })
          end
          task.delay(0.25, function()
            if tag and tag.Parent and not isMinimized then
              tw(rankLabel, 0.25, { TextTransparency = 0 })
              tw(displayNameLabel, 0.25, { TextTransparency = 0 })
            end
          end)
        end
      end
    end
  end)
end

local function applyTag(player)
  if not player or not player:IsDescendantOf(Players) then return end
  local nameLower = player.Name:lower()
  if not (player == Players.LocalPlayer or activeUsers[nameLower]) then
    clearTag(player)
    return
  end
  local customData = customTags[nameLower]
  if customData then
    createTagUI(player, "custom", customData)
    return
  end
  local boosterRole = boosterTags[nameLower]
  if boosterRole then
    local roleData = RankData[boosterRole] or RankData[boosterRole:upper()]
    if roleData then
      createTagUI(player, "custom", roleData)
      return
    end
  end
  createTagUI(player, "Xnoctis", RankData["Xnoctis"])
end

local function refreshData()
  local customData = fetchJson(JSON_URL)
  if customData and customData.players then
    local newTags = {}
    for user, data in pairs(customData.players) do newTags[user:lower()] = data end
    customTags = newTags
  end

  local boosterData = fetchJson(BOOSTER_URL)
  if boosterData and boosterData.players then
    local newBoosterTags = {}
    for user, role in pairs(boosterData.players) do newBoosterTags[user:lower()] = role end
    boosterTags = newBoosterTags
  end

  pcall(function()
    local cacheBuster = "nocache" .. tostring(os.time()) .. tostring(math.random(1, 999999))
    local res = requestFunc({
      Url = SUPABASE_URL .. "/rest/v1/Users?select=username&username=not.eq." .. cacheBuster,
      Method = "GET",
      Headers = { ["apikey"] = SUPABASE_KEY, ["Authorization"] = "Bearer " .. SUPABASE_KEY }
    })
    if res and res.Body then
      local data = HttpService:JSONDecode(res.Body)
      if data then
        local newActiveUsers = { [Players.LocalPlayer.Name:lower()] = true }
        for _, row in ipairs(data) do
          local u = row.username
          if u then
            local parts = string.split(u, "|")
            if parts[1] and parts[2] == serverId then newActiveUsers[parts[1]:lower()] = true end
          end
        end
        activeUsers = newActiveUsers
      end
    end
  end)

  for _, plr in ipairs(Players:GetPlayers()) do task.spawn(applyTag, plr) end
end

local function setupPlayer(player)
  if charConns[player] then charConns[player]:Disconnect() end
  charConns[player] = player.CharacterAdded:Connect(function()
    task.wait(0.5)
    applyTag(player)
  end)
  if player.Character then task.spawn(applyTag, player) end
end

task.spawn(function()
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
  for _, plr in ipairs(Players:GetPlayers()) do setupPlayer(plr) end
end)

Players.PlayerAdded:Connect(function(player)
  setupPlayer(player)
  task.delay(2.5, refreshData)
end)

local function unregisterSelf()
  pcall(function()
    requestFunc({
      Url = SUPABASE_URL .. "/rest/v1/Users?username=eq." .. registerName,
      Method = "DELETE",
      Headers = { ["apikey"] = SUPABASE_KEY, ["Authorization"] = "Bearer " .. SUPABASE_KEY }
    })
  end)
end

Players.PlayerRemoving:Connect(function(player)
  if charConns[player] then
    charConns[player]:Disconnect()
    charConns[player] = nil
  end
  clearTag(player)
  if player == Players.LocalPlayer then unregisterSelf() end
end)

spawn(function()
  while task.wait(CONFIG.REFRESH_INTERVAL) do refreshData() end
end)
