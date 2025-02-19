// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineGraphFragment
// ====================================================

export interface PipelineGraphFragment_solids_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphFragment_solids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  metadata: PipelineGraphFragment_solids_definition_CompositeSolidDefinition_metadata[];
}

export interface PipelineGraphFragment_solids_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineGraphFragment_solids_definition_SolidDefinition_configDefinition_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
}

export interface PipelineGraphFragment_solids_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineGraphFragment_solids_definition_SolidDefinition_configDefinition_configType;
}

export interface PipelineGraphFragment_solids_definition_SolidDefinition {
  __typename: "SolidDefinition";
  metadata: PipelineGraphFragment_solids_definition_SolidDefinition_metadata[];
  configDefinition: PipelineGraphFragment_solids_definition_SolidDefinition_configDefinition | null;
}

export type PipelineGraphFragment_solids_definition = PipelineGraphFragment_solids_definition_CompositeSolidDefinition | PipelineGraphFragment_solids_definition_SolidDefinition;

export interface PipelineGraphFragment_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineGraphFragment_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_inputs_definition_type;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_inputs_dependsOn_definition_type;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphFragment_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineGraphFragment_solids_inputs_dependsOn_definition;
  solid: PipelineGraphFragment_solids_inputs_dependsOn_solid;
}

export interface PipelineGraphFragment_solids_inputs {
  __typename: "Input";
  definition: PipelineGraphFragment_solids_inputs_definition;
  dependsOn: PipelineGraphFragment_solids_inputs_dependsOn[];
}

export interface PipelineGraphFragment_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
}

export interface PipelineGraphFragment_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineGraphFragment_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_outputs_definition_type;
  expectations: PipelineGraphFragment_solids_outputs_definition_expectations[];
}

export interface PipelineGraphFragment_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineGraphFragment_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineGraphFragment_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineGraphFragment_solids_outputs_dependedBy_definition_type;
}

export interface PipelineGraphFragment_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineGraphFragment_solids_outputs_dependedBy_solid;
  definition: PipelineGraphFragment_solids_outputs_dependedBy_definition;
}

export interface PipelineGraphFragment_solids_outputs {
  __typename: "Output";
  definition: PipelineGraphFragment_solids_outputs_definition;
  dependedBy: PipelineGraphFragment_solids_outputs_dependedBy[];
}

export interface PipelineGraphFragment_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineGraphFragment_solids_definition;
  inputs: PipelineGraphFragment_solids_inputs[];
  outputs: PipelineGraphFragment_solids_outputs[];
}

export interface PipelineGraphFragment {
  __typename: "Pipeline";
  name: string;
  solids: PipelineGraphFragment_solids[];
}
