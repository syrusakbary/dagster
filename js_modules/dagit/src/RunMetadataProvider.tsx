import * as React from "react";
import produce from "immer";
import gql from "graphql-tag";

import { RunMetadataProviderMessageFragment } from "./types/RunMetadataProviderMessageFragment";

export enum IStepState {
  WAITING = "waiting",
  RUNNING = "running",
  SUCCEEDED = "succeeded",
  SKIPPED = "skipped",
  FAILED = "failed"
}

export enum IExpectationResultStatus {
  PASSED = "Passed",
  FAILED = "Failed"
}

export enum IStepDisplayIconType {
  SUCCESS = "dot-success",
  FAILURE = "dot-failure",
  PENDING = "dot-pending",
  FILE = "file",
  LINK = "link",
  NONE = "none"
}

export enum IStepDisplayActionType {
  OPEN_IN_TAB = "open-in-tab",
  COPY = "copy",
  SHOW_IN_MODAL = "show-in-modal",
  NONE = "none"
}
export interface IStepDisplayEvent {
  icon: IStepDisplayIconType;
  text: string;
  items: {
    text: string; // shown in gray on the left
    action: IStepDisplayActionType;
    actionText: string; // shown after `text`, optionally with a click action
    actionValue: string; // value passed to the click action
  }[];
}

export interface IExpectationResult extends IStepDisplayEvent {
  status: IExpectationResultStatus;
}

export interface IMaterialization extends IStepDisplayEvent {}

export interface IStepMetadata {
  state: IStepState;
  start?: number;
  elapsed?: number;
  transitionedAt: number;
  expectationResults: IExpectationResult[];
  materializations: IMaterialization[];
}

export interface IRunMetadataDict {
  startingProcessAt?: number;
  startedProcessAt?: number;
  startedPipelineAt?: number;
  exitedAt?: number;
  processId?: number;
  initFailed?: boolean;
  steps: {
    [stepKey: string]: IStepMetadata;
  };
}

function extractMetadataFromLogs(
  logs: RunMetadataProviderMessageFragment[]
): IRunMetadataDict {
  const metadata: IRunMetadataDict = {
    steps: {}
  };

  logs.forEach(log => {
    if (log.__typename === "PipelineProcessStartEvent") {
      metadata.startingProcessAt = Number.parseInt(log.timestamp);
    }
    if (log.__typename === "PipelineProcessStartedEvent") {
      metadata.startedProcessAt = Number.parseInt(log.timestamp);
      metadata.processId = log.processId;
    }
    if (log.__typename === "PipelineStartEvent") {
      metadata.startedPipelineAt = Number.parseInt(log.timestamp);
    }
    if (log.__typename === "PipelineInitFailureEvent") {
      metadata.initFailed = true;
      metadata.exitedAt = Number.parseInt(log.timestamp);
    }
    if (
      log.__typename === "PipelineFailureEvent" ||
      log.__typename === "PipelineSuccessEvent"
    ) {
      metadata.exitedAt = Number.parseInt(log.timestamp);
    }

    if (log.step) {
      const stepKey = log.step.key;
      const timestamp = Number.parseInt(log.timestamp, 10);

      if (log.__typename === "ExecutionStepStartEvent") {
        metadata.steps[stepKey] = {
          state: IStepState.RUNNING,
          start: timestamp,
          transitionedAt: timestamp,
          expectationResults: [],
          materializations: []
        };
      } else if (log.__typename === "ExecutionStepSuccessEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {},
          step => {
            step.state = IStepState.SUCCEEDED;
            if (step.start) {
              step.transitionedAt = timestamp;
              step.elapsed = timestamp - step.start;
            }
          }
        );
      } else if (log.__typename === "ExecutionStepSkippedEvent") {
        metadata.steps[stepKey] = {
          state: IStepState.SKIPPED,
          transitionedAt: timestamp,
          expectationResults: [],
          materializations: []
        };
      } else if (log.__typename === "StepMaterializationEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {},
          step => {
            let text = (log.materialization.path || "").split("/").pop()!;
            step.materializations.push({
              icon: IStepDisplayIconType.LINK,
              text: text || "Materialization",
              items: [
                {
                  text: text,
                  actionText: "[Copy Path]",
                  action: IStepDisplayActionType.COPY,
                  actionValue: log.materialization.path || ""
                }
              ]
            });
          }
        );
      } else if (log.__typename == "StepExpectationResultEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {},
          step => {
            step.expectationResults.push({
              status: log.expectationResult.success
                ? IExpectationResultStatus.PASSED
                : IExpectationResultStatus.FAILED,
              icon: log.expectationResult.success
                ? IStepDisplayIconType.SUCCESS
                : IStepDisplayIconType.FAILURE,
              text: log.expectationResult.name
                ? log.expectationResult.name
                : "Expectation",
              items: log.expectationResult.resultMetadataJsonString
                ? [
                    {
                      text: "",
                      actionText: "[Show Metadata]",
                      action: IStepDisplayActionType.SHOW_IN_MODAL,
                      // take JSON string, parse, and then pretty print
                      actionValue: JSON.stringify(
                        JSON.parse(
                          log.expectationResult.resultMetadataJsonString
                        ),
                        null,
                        2
                      )
                    }
                  ]
                : []
            });
          }
        );
      } else if (log.__typename === "ExecutionStepFailureEvent") {
        metadata.steps[stepKey] = produce(
          metadata.steps[stepKey] || {},
          step => {
            step.state = IStepState.FAILED;
            if (step.start) {
              step.transitionedAt = timestamp;
              step.elapsed = timestamp - step.start;
            }
          }
        );
      }
    }
  });
  return metadata;
}

interface IRunMetadataProviderProps {
  logs: RunMetadataProviderMessageFragment[];
  children: (metadata: IRunMetadataDict) => React.ReactElement<any>;
}

export default class RunMetadataProvider extends React.Component<
  IRunMetadataProviderProps
> {
  static fragments = {
    RunMetadataProviderMessageFragment: gql`
      fragment RunMetadataProviderMessageFragment on PipelineRunEvent {
        __typename
        ... on MessageEvent {
          message
          timestamp
          step {
            key
          }
        }
        ... on PipelineProcessStartedEvent {
          processId
        }
        ... on StepMaterializationEvent {
          step {
            key
          }
          materialization {
            path
            description
          }
        }
        ... on StepExpectationResultEvent {
          expectationResult {
            success
            name
            resultMetadataJsonString
          }
        }
      }
    `
  };

  render() {
    return this.props.children(extractMetadataFromLogs(this.props.logs));
  }
}
