#![no_std]
#![no_main]

#[cfg(not(target_arch = "wasm32"))]
compile_error!("target arch should be wasm32: compile with '--target wasm32-unknown-unknown'");

// This code imports necessary aspects of external crates that we will use in our contract code.
extern crate alloc;

use alloc::{
    string::{String, ToString},
    vec::Vec,
};
use casper_contract::{
    contract_api::{runtime, storage},
    unwrap_or_revert::UnwrapOrRevert,
};
use casper_types::{
    addressable_entity::{EntityEntryPoint as EntryPoint, EntryPoints},
    api_error::ApiError,
    contracts::NamedKeys,
    CLType, EntryPointAccess, EntryPointPayment, EntryPointType, URef, Parameter,
};

/// Constants for the keys pointing to values stored in the account's named keys.
const CONTRACT_PACKAGE_NAME: &str = "rwa_risk_registry_package_name";
const CONTRACT_ACCESS_UREF: &str = "rwa_risk_registry_access_uref";

/// Entry point name.
const ENTRY_POINT_PUBLISH: &str = "publish_attestation";

/// Keys for values stored in contract's named keys.
const CONTRACT_VERSION_KEY: &str = "version";
const CONTRACT_KEY: &str = "rwa_risk_registry";
const REGISTRY_DICT_KEY: &str = "rwa_registry";
const LATEST_ASSET_KEY: &str = "latest_asset_id";

/// Entry point that publishes a new attestation.
#[no_mangle]
pub extern "C" fn publish_attestation() {
    let asset_id: String = runtime::get_named_arg("asset_id");
    let score_bps: u32 = runtime::get_named_arg("score_bps");
    let confidence_bps: u32 = runtime::get_named_arg("confidence_bps");
    let evidence_hash: String = runtime::get_named_arg("evidence_hash");
    let summary: String = runtime::get_named_arg("summary");
    let timestamp_ms: u64 = runtime::get_named_arg("timestamp_ms");

    // Get dictionary URef
    let dict_uref: URef = runtime::get_key(REGISTRY_DICT_KEY)
        .unwrap_or_revert_with(ApiError::MissingKey)
        .into_uref()
        .unwrap_or_revert_with(ApiError::UnexpectedKeyVariant);

    // Store each field under its own dictionary key to keep it clean and typed
    storage::dictionary_put(dict_uref, &alloc::format!("{}_score", asset_id), score_bps);
    storage::dictionary_put(dict_uref, &alloc::format!("{}_confidence", asset_id), confidence_bps);
    storage::dictionary_put(dict_uref, &alloc::format!("{}_hash", asset_id), evidence_hash);
    storage::dictionary_put(dict_uref, &alloc::format!("{}_summary", asset_id), summary);
    storage::dictionary_put(dict_uref, &alloc::format!("{}_time", asset_id), timestamp_ms);

    // Update the latest asset ID
    let latest_asset_uref: URef = runtime::get_key(LATEST_ASSET_KEY)
        .unwrap_or_revert_with(ApiError::MissingKey)
        .into_uref()
        .unwrap_or_revert_with(ApiError::UnexpectedKeyVariant);
    storage::write(latest_asset_uref, asset_id);
}

/// Entry point that executes automatically when a caller installs the contract.
#[no_mangle]
pub extern "C" fn call() {
    // Create the dictionary for registry data
    let dict_uref = storage::new_dictionary(REGISTRY_DICT_KEY).unwrap_or_revert();

    // Create URef for the latest asset ID
    let latest_asset_uref = storage::new_uref(String::new());

    // In the named keys of the contract, add keys for the dictionary and latest asset
    let mut contract_named_keys = NamedKeys::new();
    contract_named_keys.insert(String::from(REGISTRY_DICT_KEY), dict_uref.into());
    contract_named_keys.insert(String::from(LATEST_ASSET_KEY), latest_asset_uref.into());

    // Create the entry points for this contract.
    let mut entry_points = EntryPoints::new();

    let mut publish_args = Vec::new();
    publish_args.push(Parameter::new("asset_id", CLType::String));
    publish_args.push(Parameter::new("score_bps", CLType::U32));
    publish_args.push(Parameter::new("confidence_bps", CLType::U32));
    publish_args.push(Parameter::new("evidence_hash", CLType::String));
    publish_args.push(Parameter::new("summary", CLType::String));
    publish_args.push(Parameter::new("timestamp_ms", CLType::U64));

    entry_points.add_entry_point(EntryPoint::new(
        ENTRY_POINT_PUBLISH,
        publish_args,
        CLType::Unit,
        EntryPointAccess::Public,
        EntryPointType::Called,
        EntryPointPayment::Caller,
    ));

    // Create a new contract package that can be upgraded.
    let (stored_contract_hash, contract_version) = storage::new_contract(
        entry_points,
        Some(contract_named_keys),
        Some(CONTRACT_PACKAGE_NAME.to_string()),
        Some(CONTRACT_ACCESS_UREF.to_string()),
        None,
    );

    // Store the contract version in the context's named keys.
    let version_uref = storage::new_uref(contract_version);
    runtime::put_key(CONTRACT_VERSION_KEY, version_uref.into());

    // Create a named key for the contract hash under the key "rwa_risk_registry".
    // This is vital for the deployment script to retrieve the contract hash!
    runtime::put_key(CONTRACT_KEY, stored_contract_hash.into());
}
