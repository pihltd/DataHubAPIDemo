create_batch_query = """
mutation CreateBatch(
    $submissionID: ID!, 
    $type: String!, 
    $file: [FileInput]) {
  createBatch(submissionID: $submissionID, type: $type, files: $file) {
    _id
    files {
      fileName
      signedURL
    }
  }
}
"""

list_sub_query = """
query ListSubmissions($status: [String]){
  listSubmissions(status: $status){
    submissions{
      _id
      name
      submitterID
      submitterName
      studyAbbreviation
      studyID
      dbGaPID
      createdAt
      updatedAt
      metadataValidationStatus
      fileValidationStatus
      status
    }
  }
}
"""

create_submission_query = """
mutation CreateNewSubmission(
  $studyID: String!,
  $dbGaPID: String!,
  $dataCommons: String!,
  $name: String!,
  $intention:String!,
  $dataType: String!,
){
  createSubmission(
    studyID: $studyID,
    dbGaPID: $dbGaPID,
    dataCommons: $dataCommons,
    name: $name,
    intention: $intention,
    dataType: $dataType
  ){
    _id
    studyID
    dbGaPID
    dataCommons
    name
    intention
    dataType
    status
  }
}"""

org_query = """
  query GetMyUser{
    getMyUser{
      userStatus
      _id
      studies{
        _id
        studyAbbreviation
        studyName
        dbGaPID
      }
    }
  }
"""

qc_check_query = """
query GetQCResults(
  $id: ID!
  $severities: String
  $first: Int
  $offset: Int
){
  submissionQCResults(_id:$id, severities:$severities, first:$first, offset:$offset){
    total
    results{
      submissionID
      severity
      type
      errors{
        title
        description
      }
      warnings{
        title
        description
      }
    }
  }
}
"""

submission_stats_query = """
    query SubmissionStats($id: ID!) {
    submissionStats(_id: $id) {
        stats {
            nodeName
            total
            new
            passed
            warning
            error
        }
    }
}
"""

summaryQuery = """
    query SummaryQueryQCResults(
        $submissionID: ID!,
        $severity: String,
        $first: Int,
        $offset: Int,
        $orderBy: String,
        $sortDirection: String
    ){
        aggregatedSubmissionQCResults(
            submissionID: $submissionID,
            severity: $severity,
            first: $first,
            offset: $offset,
            orderBy: $orderBy
            sortDirection: $sortDirection
        ){
            total
            results{
                title
                severity
                count
                code
            }
        }
    }

"""