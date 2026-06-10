// Fill out your copyright notice in the Description page of Project Settings.


#include "AresTimeLibrary.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "Math/UnrealMathUtility.h"

// Чистая C++ замена CUDA-расчета (на случай, если сборщик выдаст ошибку на .cu file)
extern "C" void RunCudaGridCalculation(const int32* h_grid, int32 Width, int32 Height, float TileSize, float HeightZ, float* h_out_transforms)
{
    int32 total_cells = Width * Height;
    for (int32 idx = 0; idx < total_cells; ++idx)
    {
        int32 r = idx / Width;
        int32 c = idx % Width;
        h_out_transforms[idx * 3] = c * TileSize;
        h_out_transforms[idx * 3 + 1] = r * TileSize;
        h_out_transforms[idx * 3 + 2] = HeightZ;
    }
}

// Внутренний хелпер для быстрого расчета времени UDS
static void ConvertTimeInternal(float RawTime, float& OutUds, int32& OutH, int32& OutM)
{
    float Clamped = FMath::Clamp(RawTime, 0.0f, 24.0f);
    OutH = FMath::FloorToInt(Clamped);
    float Fraction = Clamped - OutH;
    OutM = FMath::RoundToInt(Fraction * 60.0f);
    if (OutM >= 60)
    {
        OutM = 0;
        OutH = (OutH + 1) % 24;
    }
    OutUds = (OutH * 100.0f) + OutM;
}

void UAresTimeLibrary::ProcessTimeOfDay(float RawTimeOfDay, float& OutUDSTime, int32& OutHours, int32& OutMinutes)
{
    ConvertTimeInternal(RawTimeOfDay, OutUDSTime, OutHours, OutMinutes);
}

bool UAresTimeLibrary::ProcessTelemetryWithCuda(
    const FString& RawJson,
    FAresAgentState& OutAgent,
    FAresEnvironmentState& OutEnvironment,
    TArray<FAresObjectState>& OutObjects,
    FString& OutShopString,
    FString& OutMissionString,
    TArray<int32>& OutTileTypes,
    TArray<FTransform>& OutTileTransforms
)
{
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(RawJson);

    // 1. Быстрый парсинг JSON на процессоре (CPU)
    if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
    {
        return false;
    }

    // =====================================================================
    // АГЕНТ (AGENT)
    // =====================================================================
    TSharedPtr<FJsonObject> AgentObj = JsonObject->GetObjectField(TEXT("agent"));
    if (AgentObj.IsValid())
    {
        OutAgent.X = AgentObj->GetIntegerField(TEXT("x"));
        OutAgent.Y = AgentObj->GetIntegerField(TEXT("y"));
        OutAgent.Direction = AgentObj->GetStringField(TEXT("direction"));
        OutAgent.Battery = AgentObj->GetNumberField(TEXT("battery"));
        OutAgent.MaxBattery = AgentObj->HasField(TEXT("max_battery")) ? AgentObj->GetNumberField(TEXT("max_battery")) : 100.0f;
        OutAgent.Capacity = AgentObj->HasField(TEXT("capacity")) ? AgentObj->GetNumberField(TEXT("capacity")) : 20.0f;
        OutAgent.CurrentWeight = AgentObj->HasField(TEXT("current_weight")) ? AgentObj->GetNumberField(TEXT("current_weight")) : 0.0f;
        OutAgent.VolumeCapacity = AgentObj->HasField(TEXT("volume_capacity")) ? AgentObj->GetNumberField(TEXT("volume_capacity")) : 16.0f;
        OutAgent.CurrentVolume = AgentObj->HasField(TEXT("current_volume")) ? AgentObj->GetNumberField(TEXT("current_volume")) : 0.0f;
        OutAgent.Status = AgentObj->GetStringField(TEXT("status"));
        OutAgent.Money = AgentObj->GetNumberField(TEXT("money"));
        OutAgent.NnThought = AgentObj->GetStringField(TEXT("nn_thought"));
        OutAgent.CameraFeedType = AgentObj->GetStringField(TEXT("camera_feed_type"));

        // Konwertujemy inwentarz (Массив -> Строka)
        TArray<TSharedPtr<FJsonValue>> InvArray = AgentObj->GetArrayField(TEXT("inventory"));
        TArray<FString> InvItems;
        for (auto Val : InvArray) InvItems.Add(Val->AsString());
        OutAgent.InventoryString = InvItems.Num() > 0 ? FString::Join(InvItems, TEXT(", ")) : TEXT("Empty");

        // Konwertujemy plan (Массив -> Строка)
        TArray<TSharedPtr<FJsonValue>> PlanArray = AgentObj->GetArrayField(TEXT("current_plan"));
        TArray<FString> PlanItems;
        for (auto Val : PlanArray) PlanItems.Add(Val->AsString());
        OutAgent.PlanString = PlanItems.Num() > 0 ? FString::Join(PlanItems, TEXT(", \n")) : TEXT("None");
    }

    // =====================================================================
    // ОКРУЖЕНИЕ (ENVIRONMENT) + МАТЕМАТИКА ВРЕМЕНИ
    // =====================================================================
    TSharedPtr<FJsonObject> EnvObj = JsonObject->GetObjectField(TEXT("environment"));
    if (EnvObj.IsValid())
    {
        OutEnvironment.StepCounter = EnvObj->GetIntegerField(TEXT("step_counter"));
        OutEnvironment.RawTimeOfDay = EnvObj->GetNumberField(TEXT("time_of_day"));
        OutEnvironment.Weather = EnvObj->GetStringField(TEXT("weather"));

        // Считаем время для неба UDS прямо в C++!
        int32 H = 0, M = 0;
        ConvertTimeInternal(OutEnvironment.RawTimeOfDay, OutEnvironment.UdsTimeOfDay, H, M);
    }

    // =====================================================================
    // ДИНАМИЧЕСКИЕ ОБЪЕКТЫ (OBJECTS)
    // =====================================================================
    OutObjects.Empty();
    TArray<TSharedPtr<FJsonValue>> ObjArray = JsonObject->GetArrayField(TEXT("objects"));
    for (auto Val : ObjArray)
    {
        TSharedPtr<FJsonObject> Obj = Val->AsObject();
        if (Obj.IsValid())
        {
            FAresObjectState NewObj;
            NewObj.Type = Obj->GetStringField(TEXT("type"));
            NewObj.X = Obj->GetIntegerField(TEXT("x"));
            NewObj.Y = Obj->GetIntegerField(TEXT("y"));
            NewObj.bIsActive = Obj->GetBoolField(TEXT("is_active"));

            // energy_pool może być null (ПОПРАВЛЕНО ДЛЯ UE 5.7)
            TSharedPtr<FJsonValue> EpValue = Obj->TryGetField(TEXT("energy_pool"));
            if (EpValue.IsValid() && !EpValue->IsNull())
            {
                NewObj.EnergyPool = EpValue->AsNumber();
            }
            else
            {
                NewObj.EnergyPool = 0.0f;
            }
            OutObjects.Add(NewObj);
        }
    }

    // =====================================================================
    // МАГАЗИН (SHOP) -> АВТОМАТИЧЕСКАЯ СБОРКА В СТРОКУ ДЛЯ HUD
    // =====================================================================
    OutShopString = TEXT("[ UPGRADE SHOP ]\n");
    TArray<TSharedPtr<FJsonValue>> ShopArray = JsonObject->GetArrayField(TEXT("shop"));
    for (auto Val : ShopArray)
    {
        TSharedPtr<FJsonObject> Item = Val->AsObject();
        if (Item.IsValid())
        {
            FString Name = Item->GetStringField(TEXT("name"));
            int32 Lvl = Item->GetIntegerField(TEXT("level"));
            float Cost = Item->GetNumberField(TEXT("next_cost_money"));
            bool bIsMaxed = Item->GetBoolField(TEXT("is_maxed"));

            if (bIsMaxed)
            {
                OutShopString += FString::Printf(TEXT("%s (Lvl %d) - MAXED\n"), *Name, Lvl);
            }
            else
            {
                OutShopString += FString::Printf(TEXT("%s (Lvl %d) - $%d\n"), *Name, Lvl, (int32)Cost);
            }
        }
    }

    // =====================================================================
    // 5. ПАРСИНГ АКТИВНОЙ МИСИИ (MISSION) -> ОПИСАНИЕ НА ЭКРАН
    // =====================================================================
    TSharedPtr<FJsonObject> MissionObj = JsonObject->GetObjectField(TEXT("mission"));
    if (MissionObj.IsValid() && MissionObj->HasField(TEXT("project_number")))
    {
        int32 ProjNum = MissionObj->GetIntegerField(TEXT("project_number"));
        FString Title = MissionObj->GetStringField(TEXT("task_title"));
        FString Algo = MissionObj->GetStringField(TEXT("algorithm"));
        OutMissionString = FString::Printf(TEXT("[ ACTIVE TASK ]\nProject #%d: %s\nAlgorithm: %s"), ProjNum, *Title, *Algo);
    }
    else
    {
        OutMissionString = TEXT("[ ACTIVE TASK ]\nDefault simulation mode");
    }

    // =====================================================================
    // СЕТКА (GRID) И ПЕРЕДАЧА НА GPU В CUDA
    // =====================================================================
    TArray<TSharedPtr<FJsonValue>> GridRows = JsonObject->GetArrayField(TEXT("grid"));
    int32 GridHeight = GridRows.Num();
    int32 GridWidth = (GridHeight > 0) ? GridRows[0]->AsArray().Num() : 0;

    OutTileTypes.Empty(); // Очищаем массив типов перед заполнением

    if (GridWidth > 0 && GridHeight > 0)
    {
        TArray<int32> FlatGrid;
        FlatGrid.SetNumUninitialized(GridWidth * GridHeight);

        for (int32 r = 0; r < GridHeight; ++r)
        {
            TArray<TSharedPtr<FJsonValue>> RowCells = GridRows[r]->AsArray();
            for (int32 c = 0; c < GridWidth; ++c)
            {
                int32 CellType = RowCells[c]->AsNumber();
                FlatGrid[r * GridWidth + c] = CellType;
                OutTileTypes.Add(CellType); // <--- Записываем тип każdej komórki dla Blueprintów!
            }
        }

        TArray<float> OutputTransforms;
        OutputTransforms.SetNumZeroed(GridWidth * GridHeight * 3);

        // Тяжелые вычисления позиций 300 kafli na karcie graficznej w CUDA
        RunCudaGridCalculation(FlatGrid.GetData(), GridWidth, GridHeight, 200.0f, 100.0f, OutputTransforms.GetData());

        OutTileTransforms.Empty();
        for (int32 i = 0; i < GridWidth * GridHeight; ++i)
        {
            FVector Location(OutputTransforms[i * 3], OutputTransforms[i * 3 + 1], OutputTransforms[i * 3 + 2]);
            OutTileTransforms.Add(FTransform(FRotator::ZeroRotator, Location, FVector(1.0f)));
        }
    }

    return true;
}

FTransform UAresTimeLibrary::CalculateTileTransform(int32 Row, int32 Column, float TileSize, float Height)
{
    float XPos = Column * TileSize;
    float YPos = Row * TileSize;
    return FTransform(FRotator::ZeroRotator, FVector(XPos, YPos, Height), FVector(1.0f));
}

void UAresTimeLibrary::GetTileVisuals(int32 TerrainType, FVector& OutScale, FVector& OutRelativeLocation)
{
    OutScale = FVector(1.0f, 1.0f, 1.0f);
    OutRelativeLocation = FVector(0.0f, 0.0f, 0.0f);

    switch (TerrainType)
    {
    case 0: // Sand
        OutScale = FVector(1.3f, 1.3f, 1.0f);
        break;
    case 1: // Rock
        OutScale = FVector(1.15f, 1.15f, 0.5f);
        break;
    case 2: // Crater
        OutScale = FVector(1.0f, 1.0f, 1.5f);
        OutRelativeLocation = FVector(0.0f, 0.0f, 5.0f);
        break;
    default:
        break;
    }
}