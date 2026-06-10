// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AresTimeLibrary.generated.h"

// Чистая структура динамических объектов на карте (Минералы, Зарядки, Баza)
USTRUCT(BlueprintType)
struct FAresObjectState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString Type = "SAND";

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    int32 X = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    int32 Y = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    bool bIsActive = false;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float EnergyPool = 0.0f;
};

// Чистая структура параметров Ровера
USTRUCT(BlueprintType)
struct FAresAgentState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    int32 X = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    int32 Y = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString Direction = "N";

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float Battery = 100.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float MaxBattery = 100.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString InventoryString = "Empty"; // Inwentarz, sklejony przez C++ w jedną linię

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float Capacity = 20.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float CurrentWeight = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float VolumeCapacity = 16.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float CurrentVolume = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString Status = "IDLE";

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString PlanString = "None"; // Plan marszruty, sklejony przez C++

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float Money = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString NnThought = "";

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString CameraFeedType = "SAND";
};

// Чистая структура параметров Окружения (Время, Погода)
USTRUCT(BlueprintType)
struct FAresEnvironmentState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    int32 StepCounter = 0;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float RawTimeOfDay = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    float UdsTimeOfDay = 0.0f; // Przeliczone C++ czas dla nieba UDS (np. 945.0)

    UPROPERTY(BlueprintReadOnly, Category = "Ares")
    FString Weather = "Clear_Skies";
};

UCLASS()
class FRONTEND_UE_API UAresTimeLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /**
     * Przyjmuje surowy JSON od Pythona, parsuje wszystkie dane na CPU (C++),
     * automatycznie oblicza czas dla UDS, generuje opis misji i wysyła siatkę na GPU do CUDA.
     */
    UFUNCTION(BlueprintCallable, Category = "Ares|GPU")
    static bool ProcessTelemetryWithCuda(
        const FString& RawJson,
        FAresAgentState& OutAgent,
        FAresEnvironmentState& OutEnvironment,
        TArray<FAresObjectState>& OutObjects,
        FString& OutShopString,
        FString& OutMissionString,           // <--- НОВОЕ ПОЛЕ: Описание активного задания
        TArray<int32>& OutTileTypes,
        TArray<FTransform>& OutTileTransforms
    );

    // Дополнительные функции (остаются для совместимости):
    UFUNCTION(BlueprintCallable, Category = "Ares|Time")
    static void ProcessTimeOfDay(float RawTimeOfDay, float& OutUDSTime, int32& OutHours, int32& OutMinutes);

    UFUNCTION(BlueprintPure, Category = "Ares|Grid")
    static FTransform CalculateTileTransform(int32 Row, int32 Column, float TileSize = 200.0f, float Height = 100.0f);

    UFUNCTION(BlueprintCallable, Category = "Ares|Grid")
    static void GetTileVisuals(int32 TerrainType, FVector& OutScale, FVector& OutRelativeLocation);
};