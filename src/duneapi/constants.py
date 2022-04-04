"""
Post data associated with Dune Analytics API
"""
# pylint: disable-msg=R0801
FIND_DASHBOARD_POST = """
    query FindDashboard($session_id: Int, $user: String!, $slug: String!) {
      dashboards(where: {slug: {_eq: $slug}, user: {name: {_eq: $user}}}) {
        ...Dashboard
        favorite_dashboards(where: {user_id: {_eq: $session_id}}, limit: 1) {
          created_at
        }
      }
    }
    
    fragment Dashboard on dashboards {
      id
      name
      slug
      private_to_group_id
      is_archived
      created_at
      updated_at
      tags
      user {
        ...User
      }
      text_widgets {
        id
        created_at
        updated_at
        text
        options
      }
      visualization_widgets {
        id
        created_at
        updated_at
        options
        visualization {
          ...Visualization
        }
      }
      param_widgets {
        id
        key
        visualization_widget_id
        query_id
        dashboard_id
        options
        created_at
        updated_at
      }
      dashboard_favorite_count_all {
        favorite_count
      }
      trending_scores {
        score_1h
        score_4h
        score_24h
        updated_at
      }
    }
    
    fragment User on users {
      id
      name
      profile_image_url
      }
    
    fragment Visualization on visualizations {
      id
      type
      name
      options
      created_at
      query_details {
        query_id
        name
        description
        user_id
        user_name
        profile_image_url
        show_watermark
        parameters
      }
    }
"""

FIND_QUERY_POST = """
    query FindQuery(
        $session_id: Int, 
        $id: Int!, 
        $favs_last_24h: Boolean! = false, 
        $favs_last_7d: Boolean! = false, 
        $favs_last_30d: Boolean! = false, 
        $favs_all_time: Boolean! = true
    ) {
      queries(where: {id: {_eq: $id}}) {
        ...Query
        favorite_queries(where: {user_id: {_eq: $session_id}}, limit: 1) {
          created_at
        }
      }
    }
    
    fragment Query on queries {
      ...BaseQuery
      ...QueryVisualizations
      ...QueryForked
      ...QueryUsers
      ...QueryFavorites
    }
    
    fragment BaseQuery on queries {
      id
      dataset_id
      name
      description
      query
      private_to_group_id
      is_temp
      is_archived
      created_at
      updated_at
      schedule
      tags
      parameters
    }
    
    fragment QueryVisualizations on queries {
      visualizations {
        id
        type
        name
        options
        created_at
      }
    }
    
    fragment QueryForked on queries {
      forked_query {
        id
        name
        user {
          name
        }
      }
    }
    
    fragment QueryUsers on queries {
      user {
        ...User
      }
    }
    
    fragment User on users {
      id
      name
      profile_image_url
    }
    
    fragment QueryFavorites on queries {
      query_favorite_count_all @include(if: $favs_all_time) {
        favorite_count
      }
      query_favorite_count_last_24h @include(if: $favs_last_24h) {
        favorite_count
      }
      query_favorite_count_last_7d @include(if: $favs_last_7d) {
        favorite_count
      }
      query_favorite_count_last_30d @include(if: $favs_last_30d) {
        favorite_count
      }
    }
"""
