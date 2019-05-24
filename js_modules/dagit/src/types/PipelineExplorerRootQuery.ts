// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PipelineExplorerRootQuery
// ====================================================

export interface PipelineExplorerRootQuery_pipeline_solids_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  metadata: PipelineExplorerRootQuery_pipeline_solids_definition_CompositeSolidDefinition_metadata[];
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes = PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes = PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  name: string | null;
  description: string | null;
  key: string;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType = PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_EnumConfigType | PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition_configType;
}

export interface PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition {
  __typename: "SolidDefinition";
  metadata: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_metadata[];
  configDefinition: PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition_configDefinition | null;
  description: string | null;
}

export type PipelineExplorerRootQuery_pipeline_solids_definition = PipelineExplorerRootQuery_pipeline_solids_definition_CompositeSolidDefinition | PipelineExplorerRootQuery_pipeline_solids_definition_SolidDefinition;

export interface PipelineExplorerRootQuery_pipeline_solids_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
  name: string | null;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipeline_solids_inputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipeline_solids_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipeline_solids_inputs_definition_type;
  description: string | null;
  expectations: PipelineExplorerRootQuery_pipeline_solids_inputs_definition_expectations[];
}

export interface PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn_definition_type;
}

export interface PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn_definition;
  solid: PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn_solid;
}

export interface PipelineExplorerRootQuery_pipeline_solids_inputs {
  __typename: "Input";
  definition: PipelineExplorerRootQuery_pipeline_solids_inputs_definition;
  dependsOn: PipelineExplorerRootQuery_pipeline_solids_inputs_dependsOn[];
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  isNothing: boolean;
  name: string | null;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs_definition_expectations {
  __typename: "Expectation";
  name: string;
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipeline_solids_outputs_definition_type;
  expectations: PipelineExplorerRootQuery_pipeline_solids_outputs_definition_expectations[];
  description: string | null;
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
  type: PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy_definition_type;
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy {
  __typename: "Input";
  solid: PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy_solid;
  definition: PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy_definition;
}

export interface PipelineExplorerRootQuery_pipeline_solids_outputs {
  __typename: "Output";
  definition: PipelineExplorerRootQuery_pipeline_solids_outputs_definition;
  dependedBy: PipelineExplorerRootQuery_pipeline_solids_outputs_dependedBy[];
}

export interface PipelineExplorerRootQuery_pipeline_solids {
  __typename: "Solid";
  name: string;
  definition: PipelineExplorerRootQuery_pipeline_solids_definition;
  inputs: PipelineExplorerRootQuery_pipeline_solids_inputs[];
  outputs: PipelineExplorerRootQuery_pipeline_solids_outputs[];
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes = PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType = PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_EnumConfigType | PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_modes_resources_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipeline_modes_resources_configField_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_resources {
  __typename: "Resource";
  name: string;
  description: string | null;
  configField: PipelineExplorerRootQuery_pipeline_modes_resources_configField | null;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes = PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType {
  __typename: "EnumConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType_innerTypes[];
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes = PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_EnumConfigType | PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_fields_configType {
  __typename: "EnumConfigType" | "CompositeConfigType" | "RegularConfigType" | "ListConfigType" | "NullableConfigType";
  key: string;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configType: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_fields_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  name: string | null;
  description: string | null;
  isList: boolean;
  isNullable: boolean;
  isSelector: boolean;
  innerTypes: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_innerTypes[];
  fields: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType_fields[];
}

export type PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType = PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_EnumConfigType | PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType_CompositeConfigType;

export interface PipelineExplorerRootQuery_pipeline_modes_loggers_configField {
  __typename: "ConfigTypeField";
  configType: PipelineExplorerRootQuery_pipeline_modes_loggers_configField_configType;
}

export interface PipelineExplorerRootQuery_pipeline_modes_loggers {
  __typename: "Logger";
  name: string;
  description: string | null;
  configField: PipelineExplorerRootQuery_pipeline_modes_loggers_configField | null;
}

export interface PipelineExplorerRootQuery_pipeline_modes {
  __typename: "Mode";
  name: string;
  description: string | null;
  resources: PipelineExplorerRootQuery_pipeline_modes_resources[];
  loggers: PipelineExplorerRootQuery_pipeline_modes_loggers[];
}

export interface PipelineExplorerRootQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  description: string | null;
  solids: PipelineExplorerRootQuery_pipeline_solids[];
  modes: PipelineExplorerRootQuery_pipeline_modes[];
}

export interface PipelineExplorerRootQuery {
  pipeline: PipelineExplorerRootQuery_pipeline;
}

export interface PipelineExplorerRootQueryVariables {
  name: string;
}
