// Fill out your copyright notice in the Description page of Project Settings.

using UnrealBuildTool;
using System.Collections.Generic;

public class frontend_ueTarget : TargetRules
{
	public frontend_ueTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V6;

		ExtraModuleNames.AddRange( new string[] { "frontend_ue" } );
	}
}
