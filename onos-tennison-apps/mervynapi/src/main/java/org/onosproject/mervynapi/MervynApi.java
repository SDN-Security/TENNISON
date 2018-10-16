
/*
 * Copyright 2015 Open Networking Laboratory
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.onosproject.mervynapi;

import org.onosproject.snort.SnortService;

import org.onosproject.ipfix.IpfixService;
import org.onosproject.rest.AbstractWebResource;
import org.slf4j.Logger;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

//import com.google.gson.Gson;



import static org.slf4j.LoggerFactory.getLogger;

/**
 * Handles Rest API call.
 */
@Path("mervyn")
public class MervynApi extends AbstractWebResource {

    private static final Logger log = getLogger(MervynApi.class);

    public MervynApi() {
    }

    /**
     * Adds reference to a snort instance to be discovered on the network.
     * TODO (l.fawcett1@lancaster.ac.uk) Return code should reflect whether or not the instance was found.
     * @param newSnortIp
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/snort/add/{ip}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response addSnort(@PathParam("ip") String newSnortIp) {
        log.info("Snort /add");

        try {
            SnortService snortService = get(SnortService.class);
            snortService.addSnortInstance(newSnortIp);
            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Add snort failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Add snort failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Removes all references to snort instances.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/snort/clear")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response clearSnort() {
        log.info("Snort /clear");

        try {
            SnortService snortService = get(SnortService.class);
            snortService.clearSnortInstances();
            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Clear snort failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Clear snort failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Removes reference to a specific snort instance.
     * TODO (l.fawcett1@lancaster.ac.uk) Return code should reflect whether the snort instance existed.
     * @param snortIp
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/snort/delete/{ip}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response delSnort(@PathParam("ip") String snortIp) {
        log.info("Snort /del");

        try {
            SnortService snortService = get(SnortService.class);
            snortService.removeSnortInstance(snortIp);
            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Delete snort failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Delete snort failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Get all the snort instances that have been successfully discovered.
     * TODO (l.fawcett1@lancaster.ac.uk) Also return instances that are still to be discovered with a pending flag.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/snort/query")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response querySnort() {
        log.info("Snort /query");
        log.warn("Method querySnort() not implemented");

        try {
            SnortService snortService = get(SnortService.class);
            return Response.ok("{Not implemented}").build();
        } catch (NullPointerException e) {
            log.error("Query snort failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Query snort failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }


    /**
     * Get all the flows installed in all the switches from the IPFIX Service.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/ipfix/query")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response queryAllFlows() {
        log.info("Ipfix  /query");

        try {
            IpfixService ipfixService = get(IpfixService.class);
            ipfixService.getFlowEntries();
            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Create Port failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Get flows installed in all the switches from the IPFIX Service, matching the 5-tuple.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/ipfix/query/flow/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response queryFlow(@PathParam("saddr") String saddr, @PathParam("daddr") String daddr,
                              @PathParam("sport") String sport, @PathParam("dport") String dport,
                              @PathParam("protocol") String protocol) {
        log.info("Ipfix /query/flow/{saddr}/{sport}/{daddr}/{dport}/{protocol}");
        try {
            IpfixService ipfixService = get(IpfixService.class);
            ipfixService.getFlowEntry(saddr, sport, daddr, dport, protocol);
            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Create Port failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Get all the flows installed in all the switches from the IPFIX Service.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/ipfix/add/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response addIpfix(@PathParam("saddr") String saddr, @PathParam("daddr") String daddr,
                             @PathParam("sport") String sport, @PathParam("dport") String dport,
                             @PathParam("protocol") String protocol) {
        log.info("Ipfix /add");

        try {
            // TODO (l.fawcett1@lancaster.ac.uk) Check format of parameters here. No wildcards allowed.
            IpfixService ipfixService = get(IpfixService.class);
            ipfixService.addIpfix(saddr, sport, daddr, dport, protocol);
            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Add ipfix failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Add a mirror rule matching the 5-tuple to all switches, * is a wild card.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/mirror/add/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response addSnortRule(@PathParam("saddr") String saddr,
                                 @PathParam("daddr") String daddr, @PathParam("sport") String sport,
                                 @PathParam("dport") String dport, @PathParam("protocol") String protocol) {
        log.info("addSnortRule()");
        try {
            SnortService snortService = get(SnortService.class);
            snortService.addMirrorRule(saddr, daddr, sport, dport, protocol, 20);

            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Create Port failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Delete a mirror rule matching the 5-tuple to all switches, * is a wild card.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/mirror/delete/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response deleteSnortRule(@PathParam("saddr") String saddr,
                                    @PathParam("daddr") String daddr, @PathParam("sport") String sport,
                                    @PathParam("dport") String dport, @PathParam("protocol") String protocol) {
        log.info("deleteSnortRule()");
        try {
            SnortService snortService = get(SnortService.class);
            snortService.deleteMirrorRule(saddr, daddr, sport, dport, protocol, 0);

            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Create Port failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Add a block rule matching the 5-tuple to all switches, * is a wild card.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/block/add/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response addBlockRule(@PathParam("saddr") String saddr,
                                 @PathParam("daddr") String daddr, @PathParam("sport") String sport,
                                 @PathParam("dport") String dport, @PathParam("protocol") String protocol) {
        log.info("addBlockRule()");
        try {
            SnortService snortService = get(SnortService.class);
            snortService.addBlockRule(saddr, daddr, sport, dport, protocol, 30);

            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Add block failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Delete a block rule matching the 5-tuple to all switches, * is a wild card.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/block/delete/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response deleteBlockRule(@PathParam("saddr") String saddr,
                                    @PathParam("daddr") String daddr, @PathParam("sport") String sport,
                                    @PathParam("dport") String dport, @PathParam("protocol") String protocol) {
        log.info("deleteBlockRule()");
        try {
            SnortService snortService = get(SnortService.class);
            snortService.deleteBlockRule(saddr, daddr, sport, dport, protocol, 0);

            return Response.ok("{\"response\":\"ok\"}").build();
        }  catch (NullPointerException e) {
            log.error("Create Port failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Add a redirect rule matching the 5-tuple to all switches, * is a wild card.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/redirect/add/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response addRedirectRule(@PathParam("saddr") String saddr,
                                 @PathParam("daddr") String daddr, @PathParam("sport") String sport,
                                 @PathParam("dport") String dport, @PathParam("protocol") String protocol) {
        log.info("addRedirectRule()");
        try {
            SnortService snortService = get(SnortService.class);
            snortService.addRedirectRule(saddr, daddr, sport, dport, protocol, 0);

            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Create Port failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }

    /**
     * Delete a redirect rule matching the 5-tuple to all switches, * is a wild card.
     * @return HTTP Response. 200 on success, 501 otherwise.
     */
    @Path("/redirect/delete/{saddr}/{sport}/{daddr}/{dport}/{protocol}")
    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response deleteRedirectRule(@PathParam("saddr") String saddr,
                                    @PathParam("daddr") String daddr, @PathParam("sport") String sport,
                                    @PathParam("dport") String dport, @PathParam("protocol") String protocol) {
        log.info("deleteRedirectRule()");
        try {
            SnortService snortService = get(SnortService.class);
            snortService.deleteRedirectRule(saddr, daddr, sport, dport, protocol, 0);

            return Response.ok("{\"response\":\"ok\"}").build();
        } catch (NullPointerException e) {
            log.error("Create Port failed because of Null Pointer Exception {}", e.getMessage());
            return Response.serverError().build();
        } catch (Exception e) {
            log.error("Create Port failed because of exception {}", e.getMessage());
            return Response.serverError().build();
        }
    }
}

